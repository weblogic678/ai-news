"""Read-only GitHub API access. Never executes fetched repository content."""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


class FetchError(RuntimeError):
    pass


def check_repo(repo):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or any(x in (".", "..") for x in repo.split("/")):
        raise ValueError("仓库须为 owner/name，不能包含URL、空格或路径跳转")
    return repo


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FetchError("接口重定向被拒绝；请核实仓库是否改名后使用新地址")


class GitHub:
    def __init__(self, timeout=20):
        self.timeout = timeout
        self.opener = urllib.request.build_opener(NoRedirect())

    def get(self, path, optional=False):
        if not path.startswith("/") or "://" in path:
            raise ValueError("仅允许固定GitHub API路径")
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "g2x-evidence/0.1", "X-GitHub-Api-Version": "2022-11-28"}
        token = os.getenv("GITHUB_TOKEN", "")
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request("https://api.github.com" + path, headers=headers)
        for attempt in range(3):
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    body = response.read(20_000_001)
                    if len(body) > 20_000_000:
                        raise FetchError("GitHub响应超过20MB，停止下载")
                    return json.loads(body)
            except urllib.error.HTTPError as exc:
                if exc.code == 404 and optional:
                    return None
                if exc.code in (403, 429):
                    retry = exc.headers.get("Retry-After", "")
                    reset = exc.headers.get("X-RateLimit-Reset", "")
                    raise FetchError(f"GitHub限流或权限不足（HTTP {exc.code}）；Retry-After={retry}, reset={reset}。未继续重试。") from None
                if exc.code >= 500 and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise FetchError(f"GitHub HTTP {exc.code}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise FetchError("GitHub网络访问失败，请检查代理或稍后重试") from None
        raise FetchError("GitHub请求失败")

    def content(self, repo, path, sha):
        item = self.get(f"/repos/{repo}/contents/{urllib.parse.quote(path, safe='/')}?ref={sha}", optional=True)
        if not isinstance(item, dict) or item.get("encoding") != "base64":
            return None
        if item.get("size", 0) > 250_000:
            return None
        text = base64.b64decode(item["content"]).decode("utf-8", errors="replace")
        return {"path": path, "blob_sha": item["sha"], "text": text,
                "url": f"https://github.com/{repo}/blob/{sha}/{urllib.parse.quote(path, safe='/')}"}

    def snapshot(self, repo):
        repo = check_repo(repo)
        meta = self.get(f"/repos/{repo}")
        release = self.get(f"/repos/{repo}/releases/latest", optional=True)
        ref = release["tag_name"] if release else meta["default_branch"]
        commit = self.get(f"/repos/{repo}/commits/{urllib.parse.quote(ref, safe='')}")
        sha = commit["sha"]
        tree = self.get(f"/repos/{repo}/git/trees/{sha}?recursive=1")
        paths = [x["path"] for x in tree.get("tree", []) if x["type"] == "blob"]
        root_licenses = [p for p in paths if "/" not in p and re.match(r"(?i)^(license|licence|copying|notice)(\.|$)", p)]
        # Read root evidence, do not mistake this for a full transitive dependency audit.
        files = [self.content(repo, p, sha) for p in root_licenses[:8]]
        readme_path = next((p for p in paths if "/" not in p and re.match(r"(?i)^readme(\.|$)", p)), None)
        readme = self.content(repo, readme_path, sha) if readme_path else None
        return {
            "schema": 1, "repo": repo, "fetched_at": datetime.now(timezone.utc).isoformat(),
            "sha": sha, "version": ref, "version_kind": "release" if release else "branch_commit",
            "metadata": {k: meta.get(k) for k in ("full_name", "description", "html_url", "archived", "pushed_at", "stargazers_count", "license", "default_branch")},
            "commit_date": commit["commit"]["committer"]["date"],
            "release": None if not release else {"tag": ref, "published_at": release["published_at"], "url": release["html_url"], "assets": [{"name": a["name"], "size": a["size"], "url": a["browser_download_url"], "digest": a.get("digest")} for a in release["assets"]]},
            "license_files": [f for f in files if f], "readme": readme,
            "tree": paths, "tree_truncated": bool(tree.get("truncated")),
            "root_evidence_complete": len(root_licenses) <= 8 and all(files),
            "scope": "主项目根目录声明与文件清单；不包括完整依赖/二进制/素材审核",
        }

    def discover(self, query, limit=10):
        query = query.strip()
        if not query or len(query) > 300:
            raise ValueError("搜索条件需为1—300字符")
        result = self.get("/search/repositories?" + urllib.parse.urlencode({"q": query, "per_page": min(max(limit, 1), 30), "sort": "updated"}))
        return [{"repo": x["full_name"], "description": x["description"], "license": (x.get("license") or {}).get("spdx_id"), "stars": x["stargazers_count"], "url": x["html_url"]} for x in result["items"]]
