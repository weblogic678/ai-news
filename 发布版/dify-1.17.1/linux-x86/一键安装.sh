#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
sha256sum -c - <<'CHECKS'
d5a411015947543b0c408da6b387d7bc416546080b0fc1246ef76ea2dd0348a3  dify-1.17.1-linux-x86-offline.part001.gz
05ad0c34220420ebb63394cf531a225f1e2ef4d4572b7c3bc9e059e4e66216ac  dify-1.17.1-linux-x86-offline.part002.gz
305152ea372761cc18bbf9e24127e2b41e809677797b23d1c0d58d318550c48a  dify-1.17.1-linux-x86-offline.part003.gz
d8f33c4d6e147e7137448cb1b5a0ff573cefd5bdd9c411689edbda42770f027e  dify-1.17.1-linux-x86-offline.part004.gz
bda26bc655a00c79d97185dcf24ad9e2b936e493ba40f55838612ffb51df62df  dify-1.17.1-linux-x86-offline.part005.gz
901f7f668d5280b2178d21e6d757ef6d556636a539a3b59cfb25eb96708bd18d  dify-1.17.1-linux-x86-offline.part006.gz
a1a955e851e8ce417e5d97bf37c1af6b64306bbed028f6fa2b022dd15aeb74f0  dify-1.17.1-linux-x86-offline.part007.gz
6c42453221dae401bcf7be78cd2572710be614a235d3f81a0e827bb6499874f6  dify-1.17.1-linux-x86-offline.part008.gz
e26a0c5f864e77f03e3d29c6de91daf95f07a158666343afe41fec67a601e74d  dify-1.17.1-linux-x86-offline.part009.gz
cf05b23062e286356dd3e158382d1d7fb56849056e739f5c29a3bb57dddc296e  dify-1.17.1-linux-x86-offline.part010.gz
5917844de0f16913453d9f7bca94208f4ae7ade0a69c8ff811b8551dc89a570a  dify-1.17.1-linux-x86-offline.part011.gz
692e700b091e655cb7fabe61fb6098ed8acd90777d526da2c6bbf0d3d909369b  dify-1.17.1-linux-x86-offline.part012.gz
46efe36c093a746e74f90c05458fce49fa96c299c375aeb848097c1367db4972  dify-1.17.1-linux-x86-offline.part013.gz
9cdefe1dd5eb00bd02f856228e1f49c835c5d6ee082f7912931a66c5f60312a0  dify-1.17.1-linux-x86-offline.part014.gz
f4438f69ce5af69a2578e26737a8be9530b54c92b41519182f68e2eb82ea4351  dify-1.17.1-linux-x86-offline.part015.gz
327eb436f214179c7ac1b13d666b12bb90e182b02cca66fad6edaaa5055be01c  dify-1.17.1-linux-x86-offline.part016.gz
40476f9c8c40d3ca379c02e78b6afda62fc1211aaf64bdd5821085e18cb8f10b  dify-1.17.1-linux-x86-offline.part017.gz
1e1f506dd953a3b030657f5a24636ce48daff95491d48e98564146a31cc70612  dify-1.17.1-linux-x86-offline.part018.gz
72db04a4f6fe87bc07a2b99e0a667298200c754a5fd47ef346017daca77dee4d  dify-1.17.1-linux-x86-offline.part019.gz
038bee1d199611859832971770e5c4fb740256fef4b358fc0fbcfc986b1b2d96  dify-1.17.1-linux-x86-offline.part020.gz
717ad3688fce1783c5bac1c4ef4a6afacdecd82caaf48e3b7a961d9827adc945  dify-1.17.1-linux-x86-offline.part021.gz
574daf5a0e1a57403a6153453314f5ff0bc6c0d362f28b0ee7cdb132e2b84fb8  dify-1.17.1-linux-x86-offline.part022.gz
781cf3a13072be9003355db23030b93005e4b9ff16c5447547e33a56a3838b1a  dify-1.17.1-linux-x86-offline.part023.gz
4b9af9fffb2893672095359f85d97d553e19c4e1b5086ec0453aa2171217f536  dify-1.17.1-linux-x86-offline.part024.gz
f77d55d6681619de7dcecba979f9402ae18e5d6cb8ff4896f24ef8a4b080ce24  dify-1.17.1-linux-x86-offline.part025.gz
0c6b59c5cae581b193f0e31398c08c8012ea6b589e30bafe97a0ea380762f043  dify-1.17.1-linux-x86-offline.part026.gz
91cbe0288b261f8f5d4ac3671065cea7509bd86dfc726ea68b4765c1fae8faeb  dify-1.17.1-linux-x86-offline.part027.gz
58e0e58261da6eaad69a3266ca6a6b32f77a14aebce7e6a3abc58ae270663151  dify-1.17.1-linux-x86-offline.part028.gz
fa1189ca8201227a5207914b38e80efeb6efa9cccbf230143fb3f5050a5e3f4e  dify-1.17.1-linux-x86-offline.part029.gz
7c9cd6ed35cbc064b5beab9e90412e606bf66c27ba4af5e8135fda462bfaa29b  dify-1.17.1-linux-x86-offline.part030.gz
3981f261df89e2bd93be83426195ee671a06d713c41e6b5960a620f8c4c31a54  dify-1.17.1-linux-x86-offline.part031.gz
18e3da9961ed2fec9939d53d7c9cc6dbfd374a41084998671222cbcf7bc7709f  dify-1.17.1-linux-x86-offline.part032.gz
CHECKS
mkdir -p .offline-runtime/package
gzip -dc "dify-1.17.1-linux-x86-offline.part001.gz" "dify-1.17.1-linux-x86-offline.part002.gz" "dify-1.17.1-linux-x86-offline.part003.gz" "dify-1.17.1-linux-x86-offline.part004.gz" "dify-1.17.1-linux-x86-offline.part005.gz" "dify-1.17.1-linux-x86-offline.part006.gz" "dify-1.17.1-linux-x86-offline.part007.gz" "dify-1.17.1-linux-x86-offline.part008.gz" "dify-1.17.1-linux-x86-offline.part009.gz" "dify-1.17.1-linux-x86-offline.part010.gz" "dify-1.17.1-linux-x86-offline.part011.gz" "dify-1.17.1-linux-x86-offline.part012.gz" "dify-1.17.1-linux-x86-offline.part013.gz" "dify-1.17.1-linux-x86-offline.part014.gz" "dify-1.17.1-linux-x86-offline.part015.gz" "dify-1.17.1-linux-x86-offline.part016.gz" "dify-1.17.1-linux-x86-offline.part017.gz" "dify-1.17.1-linux-x86-offline.part018.gz" "dify-1.17.1-linux-x86-offline.part019.gz" "dify-1.17.1-linux-x86-offline.part020.gz" "dify-1.17.1-linux-x86-offline.part021.gz" "dify-1.17.1-linux-x86-offline.part022.gz" "dify-1.17.1-linux-x86-offline.part023.gz" "dify-1.17.1-linux-x86-offline.part024.gz" "dify-1.17.1-linux-x86-offline.part025.gz" "dify-1.17.1-linux-x86-offline.part026.gz" "dify-1.17.1-linux-x86-offline.part027.gz" "dify-1.17.1-linux-x86-offline.part028.gz" "dify-1.17.1-linux-x86-offline.part029.gz" "dify-1.17.1-linux-x86-offline.part030.gz" "dify-1.17.1-linux-x86-offline.part031.gz" "dify-1.17.1-linux-x86-offline.part032.gz" > .offline-runtime/package/payload.tar
echo 'a8465da6e5562b9387d468405b812e513c6a70a92cae7a9b24f597217a4c58bb  .offline-runtime/package/payload.tar' | sha256sum -c -
tar -xf .offline-runtime/package/payload.tar -C .offline-runtime/package
bash .offline-runtime/package/install-offline.sh "$@"
