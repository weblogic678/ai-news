"""Reachability report guards; fixtures do not prove an actual deployment."""
import importlib.util,sys,subprocess,unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'dify-1.17.1/linux-x86'))
s=importlib.util.spec_from_file_location('verify_local',ROOT/'dify-1.17.1/linux-x86/verify-local.py');V=importlib.util.module_from_spec(s);s.loader.exec_module(V)
META={'tool':'fixture','version':'1','project':'fixture','url':'http://localhost:8080'}
class Checks(unittest.TestCase):
 def test_missing_daemon_never_attempts_http(self):
  opener=Mock();run=Mock(side_effect=FileNotFoundError());report=V.inspect(META,Path('.'),run,opener)
  self.assertFalse(report['runtime_reachability_passed']);opener.open.assert_not_called()
 def test_success_still_does_not_approve_listing(self):
  run=Mock(side_effect=[Mock(stdout='1'),Mock(stdout='api\n'),Mock(stdout='[{"Service":"api","State":"running","Health":"healthy"}]')]);response=Mock(status=200);opener=Mock();opener.open.return_value.__enter__=Mock(return_value=response);opener.open.return_value.__exit__=Mock(return_value=False)
  report=V.inspect(META,Path('.'),run,opener);self.assertTrue(report['runtime_reachability_passed']);self.assertFalse(report['listing_allowed']);self.assertNotIn('stdout',report)
 def test_unhealthy_service_fails_despite_accessible_home(self):
  run=Mock(side_effect=[Mock(stdout='1'),Mock(stdout='api\n'),Mock(stdout='{"Service":"api","State":"running","Health":"unhealthy"}\n')]);response=Mock(status=200);opener=Mock();opener.open.return_value.__enter__=Mock(return_value=response);opener.open.return_value.__exit__=Mock(return_value=False)
  self.assertFalse(V.inspect(META,Path('.'),run,opener)['runtime_reachability_passed'])
 def test_private_external_url_refused(self):
  run=Mock(side_effect=[Mock(stdout='1'),Mock(stdout='api\n'),Mock(stdout='[]')]);opener=Mock()
  with self.assertRaises(RuntimeError):V.inspect(dict(META,url='http://example.com'),Path('.'),run,opener)
  opener.open.assert_not_called()
