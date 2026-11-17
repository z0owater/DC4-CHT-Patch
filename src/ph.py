"""D.C.4 Plus Harmony (DC4PHDL.exe, Circus engine) - Traditional Chinese + text fix.

Runs in the game folder, on top of the Simplified Chinese patch by acies.
Nothing from the game, the translation or Microsoft's fonts is shipped here:
everything is generated on the user's PC from their own files.

  1. backs up the Simplified patch files       -> DC4PH_CHT\\SC_backup
  2. converts the scripts to Traditional (OpenCC s2tw, character names protected)
  3. builds the game font from Windows' Microsoft JhengHei Bold (+ ♪ glyph etc.)
  4. patches DC4PHDL.exe (original kept in DC4PH_CHT\\DC4PHDL.exe.original):
       - Shift-JIS fix (garbled text on non-Japanese Windows)
       - text fix by hyther1111 (ph_textfix.py): proportional half-width letters,
         no clipped descenders, text size from FontHook.ini (EngineFontSize)
  5. writes switch scripts for CHT <-> CHS
"""
import os, sys, re, json, struct, collections
from common import say, sha16, rd, wr, find_font, ini_read, ini_get, ini_set, ini_write, ini_update
from ph_textfix import patch_exe_bytes

SC_HASHES = json.loads(r'''{"cg_asa.mes": "2646d298a546a4be","cg_cmn.mes": "c8accd192dfe1ea2","cg_hiy.mes": "cec3954f93fa312d","cg_miu.mes": "868db9670ffec5e3","cg_nin.mes": "c395d3b7d7b3ad03","cg_sii.mes": "b4d35eea487e6b76","cg_sor.mes": "97dbf07c303c149d","cg_tiy.mes": "4d84c7abfeb0fe48","dc4_asa20190406c.mes": "c34db8646d8a9805","dc4_asa20190429b.mes": "16429271c8fde6f5","dc4_asa20190429c1.mes": "b31e87cfe8a0e8cb","dc4_asa20190429c2.mes": "042f4678f88af522","dc4_asa20190429c3.mes": "fd1a3cee2f99d0c2","dc4_asa20190430b.mes": "8f4e728c29063f06","dc4_asa20190501b.mes": "5c0f2e76fe36825f","dc4_asa20190502e.mes": "d2d3f0198104f32f","dc4_asa20190503b.mes": "e87ab2529f1bcfb5","dc4_asa20190504b.mes": "b3d3475cdace69f6","dc4_asa20190505d.mes": "1c9679148bdc5949","dc4_asa20190511b.mes": "4a78880ab2800d61","dc4_asa20190513c.mes": "f20af2f61bb658de","dc4_asa20200406a.mes": "acde7008f78d8245","dc4_asu20190429b.mes": "5103170a2ff9774f","dc4_asu20190430c.mes": "a09a6e3a48a70987","dc4_asu20190430d.mes": "f52a9a7a3f5b5b1f","dc4_asu20190501c.mes": "bbef6ab95fdf1e32","dc4_asu20190502c.mes": "18b72a13acaeb56b","dc4_asu20190503b.mes": "68185fe66930b537","dc4_asu20190504c.mes": "fbe96ae8a9f59b86","dc4_asu20190505b.mes": "3a821ffa351cb1e8","dc4_asu20190505d.mes": "48560198e200e884","dc4_asu20190506b.mes": "6fc0e46013829ff3","dc4_asu20190506c.mes": "f1a8b9de5e3e9848","dc4_asu20190511b.mes": "19de51be91e18d7b","dc4_asu20190513c.mes": "8f1b221fa7b92fc7","dc4_dc99990101a.mes": "a84bf97235ff22d7","dc4_hiy20190315d1.mes": "12c0a0512a554148","dc4_hiy20190315d2.mes": "e6875b5291d2c560","dc4_hiy20190316b.mes": "038ab6b85681d289","dc4_hiy20190317b.mes": "0a30fda2b4b36622","dc4_hiy20190319c.mes": "5a1f036ba666b5e4","dc4_hiy20190321b.mes": "6cf138df4f01218f","dc4_hiy20190322b.mes": "3aff77847067888a","dc4_hiy20190323b.mes": "9742e02194ee2807","dc4_hiy20190324b.mes": "723a446e1eec77c8","dc4_hiy20190324e.mes": "994da9ff763d336c","dc4_hiy20190329b.mes": "6df18770b3c83d37","dc4_hiy20190330c.mes": "fda78a7828215e60","dc4_hiy20190330e.mes": "f38ec3c22fbc1556","dc4_hiy20190331a.mes": "8180d3a5ccfe0429","dc4_hiy20190331b.mes": "27652d83332f0bbd","dc4_hiy20190401b.mes": "57abadcc34df5aed","dc4_hiy20190403b.mes": "880254576c1f1ff7","dc4_hiy20190405c.mes": "dd2039f54dbdbecd","dc4_hiy20190408a.mes": "8c378f4edb2ac276","dc4_hiy20190408c.mes": "9654a2d732afb4a3","dc4_hiy20190409c.mes": "b14ea541722cbf7b","dc4_hiy20190411c.mes": "e5b1c02e5e8c63f4","dc4_hiy20190413b.mes": "db0401172498cd98","dc4_hiy20190415c.mes": "c6d24b37d609c17c","dc4_hiy20190416a.mes": "ffe16aeaf3092ff3","dc4_hiy20190416c.mes": "ad6c767ca42c4c8d","dc4_hiy20190417c.mes": "4fc64343006e311d","dc4_hiy20190419c.mes": "65a70be919b7a539","dc4_hiy20190420e.mes": "28e0ef56f1562c92","dc4_hiy20190422a.mes": "a2a7ce6f2fc1d282","dc4_hiy20190424c.mes": "8d65cbc4be0f6864","dc4_hiy20190424d.mes": "02f12cb4f7288f2b","dc4_hiy20190425b.mes": "665b7fd13e2af62a","dc4_hiy20190426c.mes": "31780cff38678877","dc4_hiy20190427a.mes": "e1b2ffbdcdf21564","dc4_hiy20190427b.mes": "f987554cdbac229e","dc4_hiy20190427c.mes": "903c14e9c1772c48","dc4_hiy20190428b.mes": "d15f6bf05fe97ab0","dc4_hiy20190428c.mes": "b7c225d691e67014","dc4_hiy20190430b.mes": "6dc29c0eb374194f","dc4_hiy20190430c.mes": "e4a27fb3e4eaaf17","dc4_hiy20190517c.mes": "4486136d8c676127","dc4_hiy20190518c.mes": "1b3c3bf20bf8a2a2","dc4_kyo20190204a1.mes": "cb8f647281191d04","dc4_kyo20190204a2.mes": "0e5a03fcc00b7b6d","dc4_kyo20190204a3.mes": "272a36a5418f3c8e","dc4_kyo20190204b.mes": "6d6dc3c9674d8362","dc4_kyo20190204c.mes": "281452df2690f4d5","dc4_kyo20190204e.mes": "a3da4153d111e423","dc4_kyo20190205a.mes": "eeed710c41f61610","dc4_kyo20190205b.mes": "682ad644b8432da0","dc4_kyo20190205c.mes": "0cdba25d3b7ffb41","dc4_kyo20190205e.mes": "c7d3a0398cf37d05","dc4_kyo20190206a.mes": "929a0f796b22aa7e","dc4_kyo20190206b.mes": "4a724a9ebf47fe6f","dc4_kyo20190206c.mes": "ed7ad618952ecf5d","dc4_kyo20190206e.mes": "3d984248b812d3a0","dc4_kyo20190207a.mes": "fe7388da5b984584","dc4_kyo20190207b.mes": "9a52671444dbf814","dc4_kyo20190207c.mes": "e99577ecc5e745ff","dc4_kyo20190207e.mes": "6290c26cdd7d26d6","dc4_kyo20190208a.mes": "9b3d436913e36324","dc4_kyo20190208b.mes": "169ab0df88768a05","dc4_kyo20190208c1_m0.mes": "af989a93e748f7bb","dc4_kyo20190208c1_m1.mes": "128da4bec7dd04e6","dc4_kyo20190208c1_m2.mes": "3e4dd80f7d8f9eb6","dc4_kyo20190208c1_m3.mes": "c9efca05e4d96c65","dc4_kyo20190208c1_m4.mes": "d9a49307772201e3","dc4_kyo20190208e.mes": "395f9150e3c67606","dc4_kyo20190209a.mes": "017a86ec66a73b49","dc4_kyo20190209b_m0.mes": "8ac80efbb5d5587c","dc4_kyo20190209b_m1.mes": "0e40f2a967476d5f","dc4_kyo20190209b_m2.mes": "48d7fedcdea2dd73","dc4_kyo20190209b_m3.mes": "0b4fc65ae93c3fc1","dc4_kyo20190209b_m4.mes": "8a209432a32a3fbe","dc4_kyo20190209c.mes": "f5951e029db81475","dc4_kyo20190209e.mes": "5cbeda76f58fe4b5","dc4_kyo20190210a.mes": "450c268f880aa1b1","dc4_kyo20190210b.mes": "6627a34ee85cd336","dc4_kyo20190210c.mes": "7aeb481a18691f1c","dc4_kyo20190210e.mes": "d98829e15d81e720","dc4_kyo20190211a.mes": "2787d95d8d73508d","dc4_kyo20190211b_m0.mes": "22335a7f1a8bfe3a","dc4_kyo20190211b_m1.mes": "96ac87bdef305785","dc4_kyo20190211b_m2.mes": "94ac602796e6ce5a","dc4_kyo20190211b_m3.mes": "1684567d3a76d3f5","dc4_kyo20190211b_m4.mes": "6e711b01a6110b82","dc4_kyo20190211c.mes": "9b1e5d9b694af808","dc4_kyo20190211e.mes": "19195c603863e4e4","dc4_kyo20190212a.mes": "8d669d6d805253ef","dc4_kyo20190212b.mes": "c193808fc81a6dfe","dc4_kyo20190212c_m0.mes": "774470ba7616d91b","dc4_kyo20190212c_m1.mes": "30f13c70009027b8","dc4_kyo20190212c_m2.mes": "2dd5fc3fa5167e70","dc4_kyo20190212c_m3.mes": "9af10637575df45b","dc4_kyo20190212c_m4.mes": "6b224ae6a0a46a83","dc4_kyo20190212e.mes": "d6a616c63148f67c","dc4_kyo20190213a.mes": "faa3acde6c055615","dc4_kyo20190213b.mes": "b897bd333a63797c","dc4_kyo20190213c.mes": "605e62d809f10505","dc4_kyo20190213e.mes": "dfcbd21012c4a5c3","dc4_kyo20190214a.mes": "9636d09f02d50b18","dc4_kyo20190214b.mes": "82565e3bb206d276","dc4_kyo20190214c.mes": "f7e47b60d4cf8f3e","dc4_kyo20190214d.mes": "f8b9897ee304fa0b","dc4_mia20190301a.mes": "0c65d40e563ad801","dc4_mia20190301b.mes": "1b9f32f5a5ed863b","dc4_mia20190301c.mes": "f002465c8b1f98cf","dc4_mia20190302a.mes": "6350e935034ec29e","dc4_mia20190302b.mes": "b0d99edaf235cd24","dc4_mia20190303b.mes": "42c7b592de274a1b","dc4_mia20190303c.mes": "67feba8ff2cd27f8","dc4_mia20190304a.mes": "90d74ca7536ab096","dc4_mia20190304c.mes": "ed6c117369a4d093","dc4_mia20190304d.mes": "e3af99daa6be102b","dc4_mia20190305a.mes": "8c0673d6195bcc0e","dc4_mia20190305c.mes": "77ff9bd6eae5fa97","dc4_mia20190305e.mes": "b95bc24ec77ac7f8","dc4_mia20190306c.mes": "90be35a32b34f0c8","dc4_mia20190307d.mes": "b8814736c46cdc83","dc4_mia20190307e.mes": "9bfc957520809f4c","dc4_mia20190308c.mes": "17d59042853e29f1","dc4_mia20190308e.mes": "36f488a91e2fd901","dc4_mia20190309b.mes": "b95023f4d1dc7c89","dc4_mia20190309c.mes": "b378ef398d7ea01e","dc4_mia20190309d.mes": "5611fac2bec7e22c","dc4_mia20190310b.mes": "e0386df17810f137","dc4_mia20190311c.mes": "aceeada47eceba8b","dc4_mia20190312c.mes": "5e941a3370d0b5af","dc4_mia20190313c.mes": "4e346d53d7d0862e","dc4_mia20190314b.mes": "f11d0a6386bee51a","dc4_mia20190315b.mes": "a733b23a96675ad7","dc4_mia20190315c.mes": "bd72f891c84736c0","dc4_mia20190315e.mes": "53f6626c4bac02d5","dc4_mib20190301a.mes": "379d102a0ec8224c","dc4_mib20190301c.mes": "b0bb88270b7e487b","dc4_mib20190303b.mes": "929f347a341e4494","dc4_mib20190304c.mes": "2e025ad3b72c060a","dc4_mib20190305b.mes": "f3bc2bc6e17c51f2","dc4_mib20190306c.mes": "3ee56bfbe6358dcf","dc4_mib20190307b.mes": "b41fadfce91cb2c8","dc4_mib20190308c.mes": "f5ee8cdbaf411c97","dc4_mib20190309b.mes": "264118522f5e7fe1","dc4_mib20190310b.mes": "d00574818b4dd01a","dc4_mib20190311b.mes": "5bbd6dffc0f632e3","dc4_mib20190312c.mes": "e77f2a9fbeab8cf9","dc4_mib20190313c.mes": "64047ecbf38ac8f0","dc4_mib20190314c.mes": "dbeaf61cfdb6e07e","dc4_mib20190314d.mes": "a114ebebc24677da","dc4_mib20190315b.mes": "3b619254f8141c4e","dc4_mib20190315c.mes": "164aa554c45c3fe2","dc4_mib20190315d.mes": "c9e76d240758d8b4","dc4_mic20190301a.mes": "7899870a0650f755","dc4_mic20190301b.mes": "57592008cddc6491","dc4_mic20190301c.mes": "49cb1f41a5cceb79","dc4_mic20190302c.mes": "94bddaf31bd900a7","dc4_mic20190304b.mes": "e77e1a46507c79c4","dc4_mic20190304c.mes": "539968f07e924d5c","dc4_mic20190305b.mes": "388f7bdad212e082","dc4_mic20190306c.mes": "6f1b36accb0837d6","dc4_mic20190307a.mes": "2b3209a1332ce995","dc4_mic20190307c.mes": "8ee88aacdd5a9c2b","dc4_mic20190308d.mes": "92fe1bf89aa3add8","dc4_mic20190309b.mes": "51408d11df66f56c","dc4_mic20190310b.mes": "39ec66a379892cc5","dc4_mic20190310d.mes": "5f4f65245093de06","dc4_mic20190311c.mes": "dcbc1a87bada1104","dc4_mic20190312d.mes": "b6fc7bf0b94ab5a4","dc4_mic20190313b.mes": "462927da46d9c324","dc4_mic20190314c.mes": "4512d3e24abd39bc","dc4_mic20190315b.mes": "38e8bfe7f4ca32fc","dc4_mic20190315c.mes": "a9116545d104fab7","dc4_mic20190315d.mes": "0f3a360a81df07d3","dc4_mid20190301a1.mes": "1c93fd35b77225b6","dc4_mid20190301a2.mes": "c21fe6909ff19334","dc4_mid20190301b.mes": "c82a1c7e5a83a20b","dc4_mid20190301c.mes": "8e8ec86f72afd29a","dc4_mid20190302a.mes": "58bec0ad2d0ef653","dc4_mid20190303b.mes": "a28b636c1556218f","dc4_mid20190303c.mes": "e0bb54d267079944","dc4_mid20190304a.mes": "6fbf608f8ce63a01","dc4_mid20190304c.mes": "2d56308a682e977f","dc4_mid20190304d.mes": "fa29b4112aebf354","dc4_mid20190305c.mes": "57b92c655cae9322","dc4_mid20190306c.mes": "2aae27f0bb093b9c","dc4_mid20190307c.mes": "59f3ccea6107cab2","dc4_mid20190307d.mes": "e93684423ba6566a","dc4_mid20190308c.mes": "21ded0ed3ad46518","dc4_mid20190308e.mes": "4f289433f40e6b66","dc4_mid20190309b.mes": "c35bcbaac435469d","dc4_mid20190309c.mes": "b27a4436474bc5fe","dc4_mid20190310a.mes": "c807a518d548ac84","dc4_mid20190310b.mes": "f593ea843c7f67ca","dc4_mid20190310d.mes": "1df71644ca6fa934","dc4_mid20190310e.mes": "9900ebb1665d9bf0","dc4_mid20190311a.mes": "fea830821fbe9658","dc4_mid20190312c.mes": "920151f4eef7331c","dc4_mid20190314a.mes": "8b65390e6f90e500","dc4_mid20190314c.mes": "313a0d52011e20fc","dc4_mid20190315b.mes": "8456780c20c6e820","dc4_mid20190317b.mes": "bf167ce7867c700a","dc4_mid20190321b.mes": "ea7fbbdc474c7b77","dc4_mid20190322e.mes": "464819092b2eeada","dc4_mid20190323a.mes": "975adb34bf859d23","dc4_mid20190323b.mes": "ddc72104481f79f8","dc4_mid20190324b.mes": "d406712d084558ef","dc4_mid20190326c.mes": "fd9553b88ddde277","dc4_mid20190329b.mes": "3b699c7d9f06cfff","dc4_mid20190330a.mes": "763053b368ba35cc","dc4_mid20190330b.mes": "c7e33e8b2a444527","dc4_mid20190402b.mes": "5d6e611eeaebc512","dc4_mid20190402e.mes": "ff55e1db2470b81d","dc4_mid20190403b.mes": "818de41aa6a5ba11","dc4_mid20190404b.mes": "6fccf0d38918adca","dc4_mid20190405e.mes": "d33ed3b5a6089d9d","dc4_mid20190406e.mes": "007a66b6c2e44df2","dc4_mid20190407b.mes": "864929f50df2944d","dc4_mid20190408a.mes": "1a0fd45403b94145","dc4_mid20190408c.mes": "b26cd6cdb83d5f80","dc4_mid20190409c.mes": "916878702a136faf","dc4_mid20190410b.mes": "b0907749fc4341e4","dc4_mid20190410c.mes": "24942ef36e0391b3","dc4_mid20190413b.mes": "e8b3e09b0b1704f5","dc4_mid20190413e.mes": "3321c203fba092e5","dc4_mid20190414b.mes": "2f4eeda5f41f1f8d","dc4_mid20190414e.mes": "e3af07cd3cb246e9","dc4_mid20190415c.mes": "54eb2ab9399e92d5","dc4_mid20190415e.mes": "0db38235b75041ac","dc4_mid20190416a.mes": "c1499c0a39d28423","dc4_mid20190416c.mes": "76e4e163d84f1a44","dc4_mid20190417c.mes": "ab723651ef041313","dc4_mid20190419c.mes": "cbdf900da4ad7b4c","dc4_mid20190420e.mes": "0e8fe56a923d0335","dc4_mid20190421a.mes": "e1b1ff5a8a406455","dc4_mid20190428b.mes": "b8653a6f5bd3d3fb","dc4_miu20190315d.mes": "33e647a706f4b1cc","dc4_miu20190316c.mes": "64ddcf8f7f4ed336","dc4_miu20190317a.mes": "f319f9984673a430","dc4_miu20190317b.mes": "aeed3dabfe2539b2","dc4_miu20190318b.mes": "3a1da1e5472bcad1","dc4_miu20190319c.mes": "e15dda51a08d171a","dc4_miu20190321b.mes": "b7cccdcfb772f86b","dc4_miu20190322c.mes": "270e7ce9cec6808f","dc4_miu20190323b.mes": "96b1b529127f4f43","dc4_miu20190325b.mes": "c69d9bccd6be6456","dc4_miu20190326b.mes": "a1fbe598da60f8c5","dc4_miu20190327c.mes": "3667aa0b9bc34867","dc4_miu20190328b.mes": "1fe5f978b87ddbe7","dc4_miu20190329b.mes": "d8c8fdd375284b5a","dc4_miu20190330b.mes": "69f29a8a582d1a5e","dc4_miu20190330c.mes": "6f7177bc672718fa","dc4_miu20190331c.mes": "57bcc8ba858f52e1","dc4_miu20190331c2.mes": "c1090e42f55fa842","dc4_miu20190426c.mes": "6f26d7717c2c63d4","dc4_miu20190427c.mes": "8e6a3460f82d3bc7","dc4_nin20190316a.mes": "40eee047b187f004","dc4_nin20190316b.mes": "3ebc581ffa8fbe7f","dc4_nin20190318a.mes": "a5382405abdef993","dc4_nin20190319b.mes": "af994237f6c6c052","dc4_nin20190321b.mes": "b139cc7eb0e91af2","dc4_nin20190323b.mes": "8b63bf74763ea0d8","dc4_nin20190324b.mes": "bf7df3cf6b81adbe","dc4_nin20190324c.mes": "4f7744f65cdd187d","dc4_nin20190325b.mes": "b5cd631171e49661","dc4_nin20190326b.mes": "28fb4fb0784ddd00","dc4_nin20190327b.mes": "0961e82d4b87b229","dc4_nin20190329d.mes": "f90664074f2b2494","dc4_nin20190330a.mes": "6a6717baef63c9ce","dc4_nin20190330b.mes": "a0ffa505a641b194","dc4_nin20190331b.mes": "48839c9818e958c4","dc4_nin20190401b.mes": "aa1a5a662ce948a8","dc4_nin20190402b.mes": "dfdb516541a7251f","dc4_nin20190408a.mes": "855bdca297f402eb","dc4_nin20190408c.mes": "42e0d02c144d3d28","dc4_nin20190408d.mes": "a2da674a54fe84be","dc4_nin20190409a.mes": "ef4fccbf947543f9","dc4_nin20190409c.mes": "57b21d520a8b9bf6","dc4_nin20190409d.mes": "081b442e3e4b5ee3","dc4_nin20190410a.mes": "a4268830c5f2b243","dc4_nin20190410c.mes": "19892765ea3ab02e","dc4_nin20190411a.mes": "c44f792fccfe75c3","dc4_nin20190411b.mes": "48117f8d8766a128","dc4_nin20190412b.mes": "628d274f689088c8","dc4_nin20190412c.mes": "afeec71796486f65","dc4_nin20190413c.mes": "19dfed00d327f524","dc4_nin20190414b.mes": "5fb9e7d41a903682","dc4_nin20190414c.mes": "03b30f3449ad67a4","dc4_nin20190415a.mes": "dd6d2b57fb039e13","dc4_nin20190415c.mes": "10ad66b9cbb4912d","dc4_nin20190416a.mes": "5581974a8b4e6537","dc4_nin20190416d.mes": "9fb9ebd98d9a4fdd","dc4_nin20190418c.mes": "9a4a9fa353a9e02e","dc4_nin20190420b.mes": "2a99a5378f87c6b1","dc4_nin20190421b.mes": "17adcd13c8991fd3","dc4_nin20190421c.mes": "1f989aa1c1e28670","dc4_nin20190422a.mes": "317e7508bf033804","dc4_nin20190422d.mes": "00baa3ef8af2c1bc","dc4_nin20190423a.mes": "03da89e3b6560c0a","dc4_nin20190424a.mes": "e0ddcd55527cbe5e","dc4_nin20190424d.mes": "df55d4b7097049be","dc4_nin20190425b.mes": "44296449c0258dd7","dc4_nin20190425d.mes": "43280ac9d649a22e","dc4_nin20190426b.mes": "380590cdd48add80","dc4_nin20190427a.mes": "1cf545d8ad57d5e3","dc4_nin20190427d.mes": "39379bd663bf7bb5","dc4_nin20190428b.mes": "ebfe0d29e9d76b3b","dc4_nin20190429a.mes": "c6ee1541c935e4f2","dc4_nin20190430c.mes": "a1747992bba84cfb","dc4_nin20190501a.mes": "5f6c244fccc97f83","dc4_nin20190501c.mes": "00151b93579c6b90","dc4_nin20190501d1.mes": "c6736453b1fb635b","dc4_nin20190501d2.mes": "d3157fee94a8cbae","dc4_nin20190501d3.mes": "4161ef21339654b3","dc4_nin20190503b.mes": "6bc182c20128fcc9","dc4_nin20190503d.mes": "5e9574aa8adfee1d","dc4_nin20190511b.mes": "4cb1982d29de6a2c","dc4_nin20190511c.mes": "fd38c66375d099fc","dc4_sen20181213b.mes": "e1618764f4ccf793","dc4_sen20181213c.mes": "443f08d15805565d","dc4_sen20181213d.mes": "851ed4e12cae1bb3","dc4_sen20181214a1.mes": "736a69ae379c7cac","dc4_sen20181214a2.mes": "228f55f27eb9aab7","dc4_sen20181214b.mes": "3360eaed3eab766f","dc4_sen20181214d.mes": "f938e4371dbd635c","dc4_sen20181215b.mes": "ad2ddcff07e64373","dc4_sen20181215d.mes": "bc933f12f2870151","dc4_sen20181216b.mes": "bf6e9fab410946a4","dc4_sen20181217a.mes": "31f84d634f95e157","dc4_sen20181217b.mes": "2deeae6cd53b29cd","dc4_sen20181217c.mes": "f2f5ecc729e3244b","dc4_sen20181217e.mes": "2fe8bff29ced6fb4","dc4_sen20181218b.mes": "514056060997c9c8","dc4_sen20181218c.mes": "47f9054bd4ba71ab","dc4_sen20181219b.mes": "10635fe3b745b489","dc4_sen20181219c.mes": "c435e3c29c168809","dc4_sen20181220b.mes": "2502c4f7e86d9026","dc4_sen20181220d.mes": "7b8aab0d7ea468d4","dc4_sen20181221a.mes": "9108ca71cadca847","dc4_sen20181221b.mes": "68110b64fb991849","dc4_sen20181221c.mes": "c2a818466dbfa631","dc4_sen20181222b.mes": "26201090f64ef4d4","dc4_sen20181223c.mes": "97a9e36c85cde0a9","dc4_sen20181223d.mes": "1c2f8b250b3f2c8f","dc4_sen20181224b.mes": "8566f1eec56150fa","dc4_sen20181224c1_m0.mes": "d89979899a5db013","dc4_sen20181224c1_m1.mes": "f4c71b8079c2fb1a","dc4_sen20181224c1_m2.mes": "3d91aa88e62c51de","dc4_sen20181224c1_m3.mes": "79eeaab59a38a069","dc4_sen20181224c1_m4.mes": "ee618046b71661fa","dc4_sen20181224c1_m5.mes": "40df327c7d159018","dc4_sen20181224c2.mes": "f4ff4eb22b35da1e","dc4_sen20181224d.mes": "d202d2efa10774ef","dc4_sen20181225a.mes": "26776e383dc3876b","dc4_sii20190316a.mes": "36c2e175ccfa377d","dc4_sii20190316b.mes": "5dc609eff8c77b0c","dc4_sii20190318b.mes": "071cb8ee0e562def","dc4_sii20190319c.mes": "30bde47b135b4cda","dc4_sii20190321b.mes": "3278fdcfea9994cc","dc4_sii20190322c.mes": "51155e20faaa52d7","dc4_sii20190323b.mes": "3662db80f6115ce1","dc4_sii20190325b.mes": "898f98294d4e65a0","dc4_sii20190328b.mes": "9e38712b9a46e016","dc4_sii20190329d.mes": "2011c1555837f3b4","dc4_sii20190330b.mes": "644ce8400163399d","dc4_sii20190331b.mes": "e659626051ffdbe8","dc4_sii20190402c.mes": "bc86aae1e41dab6f","dc4_sii20190404c.mes": "cda9b7f116d33961","dc4_sii20190405c.mes": "420fa41e031363d9","dc4_sii20190407a.mes": "24a33713ae8606b7","dc4_sii20190407b.mes": "f4681a754b4ae069","dc4_sii20190408d.mes": "eafef8a92e6eb8d5","dc4_sii20190409c.mes": "867d267db3a5c406","dc4_sii20190411b.mes": "27ba1f8cea744272","dc4_sii20190411c.mes": "b69f13088ef91f7f","dc4_sii20190412c.mes": "3de52cc04fcde27a","dc4_sii20190415c.mes": "6852f8b5dd6946bc","dc4_sii20190416a.mes": "a6d375078dd2b8b9","dc4_sii20190416b.mes": "78198489282d2bcd","dc4_sii20190418b.mes": "7a07b20c4d7462c7","dc4_sii20190418c.mes": "da2e8b0cc6b46a17","dc4_sii20190420d.mes": "0a9b2bdc3f8ef994","dc4_sii20190421b.mes": "66436b0e36148941","dc4_sii20190422c.mes": "d9d7cba1a0f08b36","dc4_sii20190424c.mes": "76c46d5174ad7255","dc4_sii20190427c.mes": "547c0c97baeaecb3","dc4_sii20190428c.mes": "b2c7abdb714ac3d7","dc4_sii20190501c.mes": "7d72c3dc9adbd4df","dc4_sii20190502d.mes": "ee4e02ab67be851a","dc4_sii20190503d.mes": "29dfe16f12335c08","dc4_sii20190504b.mes": "e33fd1fab6141d2e","dc4_sii20190505d.mes": "b20864e16639aa01","dc4_sii20190507c.mes": "be0cdf517a32bf35","dc4_sii20190507c2.mes": "4b1cc18a11693ec1","dc4_sii20190526b.mes": "2904cebef47540d6","dc4_sii20190527c.mes": "00da4bc0ad82482f","dc4_sor20190316a.mes": "f66cbcd3f44df108","dc4_sor20190316b.mes": "63d1422560fa58ec","dc4_sor20190317b.mes": "3905a192c4aa68b0","dc4_sor20190318d.mes": "0bd39cb1aedd9b72","dc4_sor20190319c.mes": "dc199559b8c80d2d","dc4_sor20190320a.mes": "f7280f21f8f1c82e","dc4_sor20190321b.mes": "7dca761879b0af85","dc4_sor20190322b.mes": "cb4cad1f69a0a881","dc4_sor20190323a.mes": "3b07519f54976bad","dc4_sor20190323c.mes": "589e82c2f878811d","dc4_sor20190323d.mes": "8241da132cd37728","dc4_sor20190324a.mes": "2175d0204e61d12e","dc4_sor20190324b.mes": "5798f82667f65ed7","dc4_sor20190325b.mes": "cd019e3c8a9babfc","dc4_sor20190326b.mes": "b67c56b0c6be705d","dc4_sor20190328b.mes": "c0a7392f85e31137","dc4_sor20190331b.mes": "55c99225c46c963c","dc4_sor20190403b.mes": "13b62ef172b00fb4","dc4_sor20190406b.mes": "90054639a41cd0c8","dc4_sor20190407c.mes": "6c2911c12deaee8e","dc4_sor20190408b.mes": "a62e57c0d8fdd143","dc4_sor20190408c.mes": "3ee7cc2a55fdc789","dc4_sor20190409c.mes": "5b6f3fa032ab244c","dc4_sor20190409d.mes": "9c202edd88021c6d","dc4_sor20190411c.mes": "1af920d6aa174f98","dc4_sor20190412a.mes": "afd1c04c2bfbd428","dc4_sor20190413b.mes": "48cd14e8e54e1a34","dc4_sor20190415c.mes": "e4cb108d9c6170c5","dc4_sor20190418b.mes": "96115805c627524f","dc4_sor20190419c.mes": "158a2049829012aa","dc4_sor20190420b.mes": "50f6e6d61489853b","dc4_sor20190420e.mes": "9891cf5163eab3c8","dc4_sor20190421a.mes": "11ba2591ac3c689a","dc4_sor20190421c.mes": "9cc559312507a553","dc4_sor20190422c.mes": "cafabadf5ddb8311","dc4_sor20190423a.mes": "2a409acf32f4627b","dc4_sor20190423c.mes": "7d09b02f74c4589a","dc4_sor20190424a.mes": "cb0061a0df813acf","dc4_sor20190425c.mes": "0646d5b31ee21415","dc4_sor20190427b.mes": "dc7f90b46e48420b","dc4_sor20190430b.mes": "658fea4bd52703bb","dc4_sor20190430c.mes": "db2305e0961d3727","dc4_sor20190430d.mes": "ec0991001999cf65","dc4_sor20190501a.mes": "3e9619a1a6970c78","dc4_sor20190504a.mes": "2292e76b8a8c266c","dc4_sor20190504b.mes": "dc52f2a4abb39a1b","dc4_sor20190504c.mes": "bc91920452202f7b","dc4_sor20190510c.mes": "796a4f6c15c0fb83","dc4_sor20190511c.mes": "09b73120219e0f8d","dc4_tiy20190316b.mes": "0cfe4cc33d46a073","dc4_tiy20190317b.mes": "ba4c45e23d1f2278","dc4_tiy20190320c.mes": "f229bf83dab90d0f","dc4_tiy20190321d.mes": "be2d9b0e4822dcb2","dc4_tiy20190322d.mes": "89043487a05a38ee","dc4_tiy20190323b.mes": "492dbf1755622d15","dc4_tiy20190324b.mes": "d23830215db74e21","dc4_tiy20190326b.mes": "6dc4546550788d9a","dc4_tiy20190327c.mes": "7bb3478d93fc1167","dc4_tiy20190329c.mes": "121b93fc868f575f","dc4_tiy20190329d.mes": "992f940a6866c17f","dc4_tiy20190330b.mes": "4897255f4fb93f02","dc4_tiy20190331b.mes": "8b4d9523714009f4","dc4_tiy20190401c.mes": "55b235cc0554f65d","dc4_tiy20190402c.mes": "e5677fba487a2844","dc4_tiy20190403b.mes": "31582278b0dbb94c","dc4_tiy20190404c.mes": "a50d595d0fa96fd0","dc4_tiy20190405d.mes": "40055f8e5064531c","dc4_tiy20190405d2.mes": "2505abd26405dbfc","dc4_tiy20190405d2_bk.mes": "98b91120ce63dbf6","dc4_tiy20190426d1.mes": "5fc61881a23b3ff4","dc4_tiy20190426d2.mes": "4ebf066722de4225","sce_asa.mes": "dac1e3a9cc4fce7e","sce_com.mes": "9fc9464db8550f24","sce_hiy.mes": "1b77712e634e647d","sce_miu.mes": "3bce30ecc9dfa252","sce_nin.mes": "796c28608c8a64e2","sce_sii.mes": "69eac20c58d9d877","sce_sor.mes": "f21c9c88ffec4ffc","sce_tiy.mes": "2dbb85690081885f"}''')
CHT_HASHES = json.loads(r'''{"cg_asa.mes": "2646d298a546a4be","cg_cmn.mes": "c8accd192dfe1ea2","cg_hiy.mes": "cec3954f93fa312d","cg_miu.mes": "868db9670ffec5e3","cg_nin.mes": "c395d3b7d7b3ad03","cg_sii.mes": "b4d35eea487e6b76","cg_sor.mes": "97dbf07c303c149d","cg_tiy.mes": "4d84c7abfeb0fe48","dc4_asa20190406c.mes": "d2b95bda1f157a9b","dc4_asa20190429b.mes": "e0a18cdf623a4812","dc4_asa20190429c1.mes": "1fe31f3125842e69","dc4_asa20190429c2.mes": "3a2e784efb7b8037","dc4_asa20190429c3.mes": "2bbe5d54f743cd9e","dc4_asa20190430b.mes": "9faa9551282b6105","dc4_asa20190501b.mes": "20adbb6f0b3e0a7e","dc4_asa20190502e.mes": "21a776774e9cd0e3","dc4_asa20190503b.mes": "1d1f407774be4f9d","dc4_asa20190504b.mes": "3b3dcfd962484850","dc4_asa20190505d.mes": "7a1ffc62908ce13e","dc4_asa20190511b.mes": "5736e1380f271992","dc4_asa20190513c.mes": "8a4aea61b1165da1","dc4_asa20200406a.mes": "ba534357276f85c8","dc4_asu20190429b.mes": "7aec6d5ad23135ef","dc4_asu20190430c.mes": "d05a350d3eb6157e","dc4_asu20190430d.mes": "0f1139e2c93c4878","dc4_asu20190501c.mes": "8096f961a4cd3c8e","dc4_asu20190502c.mes": "655b5cac372f6f2a","dc4_asu20190503b.mes": "90851b24086806ff","dc4_asu20190504c.mes": "8f05b578415515c4","dc4_asu20190505b.mes": "20d99c6bb4503158","dc4_asu20190505d.mes": "238dfa8fb3ee17b1","dc4_asu20190506b.mes": "6472b58382546fd2","dc4_asu20190506c.mes": "a216752b0cb884c1","dc4_asu20190511b.mes": "c3f1b59dd47a99d0","dc4_asu20190513c.mes": "89adbd5895b13c25","dc4_dc99990101a.mes": "3b25a1220145cba2","dc4_hiy20190315d1.mes": "72e8a49dd051264e","dc4_hiy20190315d2.mes": "3e7f358a2a59c511","dc4_hiy20190316b.mes": "8a20d21261b9b032","dc4_hiy20190317b.mes": "f78dee83686b020c","dc4_hiy20190319c.mes": "f5c7a70acd653923","dc4_hiy20190321b.mes": "ed5c88fcca53c190","dc4_hiy20190322b.mes": "ec9f579831714bd7","dc4_hiy20190323b.mes": "7e280a30e258c4bd","dc4_hiy20190324b.mes": "f6139f262dd90fc6","dc4_hiy20190324e.mes": "21e39ed0cec48451","dc4_hiy20190329b.mes": "15609e2ff64d9aeb","dc4_hiy20190330c.mes": "d03cf8aae38148c6","dc4_hiy20190330e.mes": "2b48b32a0ea8236f","dc4_hiy20190331a.mes": "cf2f20ea3d6c0b16","dc4_hiy20190331b.mes": "adc4c66df376c767","dc4_hiy20190401b.mes": "6a10b9d6ae437fb2","dc4_hiy20190403b.mes": "f9900bcd22d19b6d","dc4_hiy20190405c.mes": "79a94b1eeb506024","dc4_hiy20190408a.mes": "7d11d8f2a9ce8da4","dc4_hiy20190408c.mes": "8d1de7bf9ed5d0bc","dc4_hiy20190409c.mes": "9ed9114af22b0306","dc4_hiy20190411c.mes": "04a382dcbe646e5f","dc4_hiy20190413b.mes": "09111377d2b9021d","dc4_hiy20190415c.mes": "0b024fa388151d8b","dc4_hiy20190416a.mes": "ab89b5fb1a9aa5e4","dc4_hiy20190416c.mes": "28174241b3bcd339","dc4_hiy20190417c.mes": "38d278424013eaad","dc4_hiy20190419c.mes": "3e57f8812e159422","dc4_hiy20190420e.mes": "416a9ec6b754577c","dc4_hiy20190422a.mes": "fbfdd2f4a9d099c3","dc4_hiy20190424c.mes": "5a6f0c19e69fc0e1","dc4_hiy20190424d.mes": "41b8bc62e3c8cfd8","dc4_hiy20190425b.mes": "0bd5349bf15851db","dc4_hiy20190426c.mes": "7e942b4a7c002fc7","dc4_hiy20190427a.mes": "d7bf419e15b22d32","dc4_hiy20190427b.mes": "f872cea0f37d6e3b","dc4_hiy20190427c.mes": "2f7285bc8a1aab69","dc4_hiy20190428b.mes": "6215e27e7803bdf0","dc4_hiy20190428c.mes": "a03559c2f426d612","dc4_hiy20190430b.mes": "2d2c98c20a48bc99","dc4_hiy20190430c.mes": "d9c160c335bd1d74","dc4_hiy20190517c.mes": "08a9121d2fab2810","dc4_hiy20190518c.mes": "2610aed8d170c56f","dc4_kyo20190204a1.mes": "460cde53c6794fe0","dc4_kyo20190204a2.mes": "2b7ec76496e6ee79","dc4_kyo20190204a3.mes": "bd12b7e41f83d5b2","dc4_kyo20190204b.mes": "b5671b93a9ffd223","dc4_kyo20190204c.mes": "ffa9686903842aa6","dc4_kyo20190204e.mes": "bd059004d0522322","dc4_kyo20190205a.mes": "2bfef8a00e8f68c0","dc4_kyo20190205b.mes": "14a01752833c22e9","dc4_kyo20190205c.mes": "2b1ceb459ef16572","dc4_kyo20190205e.mes": "6b75105f2f177845","dc4_kyo20190206a.mes": "4e42e3cb7321f9e2","dc4_kyo20190206b.mes": "ca178b3a5597d69c","dc4_kyo20190206c.mes": "6164a5be54c3b367","dc4_kyo20190206e.mes": "b83ebf73d2c80456","dc4_kyo20190207a.mes": "8da9c90c791832af","dc4_kyo20190207b.mes": "9c10ab4d0d0e8417","dc4_kyo20190207c.mes": "29498186473d542a","dc4_kyo20190207e.mes": "4c04f3d3d6aa9ceb","dc4_kyo20190208a.mes": "f366588300cbfa25","dc4_kyo20190208b.mes": "963209bdcdb2c70b","dc4_kyo20190208c1_m0.mes": "fed754f82fc6d638","dc4_kyo20190208c1_m1.mes": "86400edd2f1dcd7c","dc4_kyo20190208c1_m2.mes": "e263804adea5952d","dc4_kyo20190208c1_m3.mes": "c9b7f4f8e5635fdc","dc4_kyo20190208c1_m4.mes": "b36444d8a21980a0","dc4_kyo20190208e.mes": "1fcac87504631c9d","dc4_kyo20190209a.mes": "68fdfcdd084be134","dc4_kyo20190209b_m0.mes": "8084454d86d5f913","dc4_kyo20190209b_m1.mes": "06dfba7f16dae7d5","dc4_kyo20190209b_m2.mes": "23a47e377c706a71","dc4_kyo20190209b_m3.mes": "5aa0ea2a0397b1ab","dc4_kyo20190209b_m4.mes": "ded29123e47b1c13","dc4_kyo20190209c.mes": "3e1d334680437013","dc4_kyo20190209e.mes": "91b25a573d245f56","dc4_kyo20190210a.mes": "09fbe11b35f36576","dc4_kyo20190210b.mes": "73c94ab509dbed2b","dc4_kyo20190210c.mes": "b2ac2b702a652707","dc4_kyo20190210e.mes": "8c9bac899e6fbf55","dc4_kyo20190211a.mes": "99518b575db02fd5","dc4_kyo20190211b_m0.mes": "e0c4f6c5759b4493","dc4_kyo20190211b_m1.mes": "d0720958cf83184c","dc4_kyo20190211b_m2.mes": "51b9213be2f8ba63","dc4_kyo20190211b_m3.mes": "1df3e3be59c78fd2","dc4_kyo20190211b_m4.mes": "555f1fa1d12098b7","dc4_kyo20190211c.mes": "c4b2a971e3b4257e","dc4_kyo20190211e.mes": "36a7c030f6d1913e","dc4_kyo20190212a.mes": "b98629a88012e7f0","dc4_kyo20190212b.mes": "2a0423eb4d7bf9e2","dc4_kyo20190212c_m0.mes": "3f2bf03cc2b773a8","dc4_kyo20190212c_m1.mes": "66776ed9d23eb9bc","dc4_kyo20190212c_m2.mes": "68db390e9ecd84bc","dc4_kyo20190212c_m3.mes": "7a36cd0b45b81a2a","dc4_kyo20190212c_m4.mes": "a44564f8efc6c47b","dc4_kyo20190212e.mes": "83348a7d839b3bd7","dc4_kyo20190213a.mes": "909ad3377159318f","dc4_kyo20190213b.mes": "e15117c02e44bf5a","dc4_kyo20190213c.mes": "9155afd23100edbd","dc4_kyo20190213e.mes": "b159182670e3b332","dc4_kyo20190214a.mes": "d20ef92044733535","dc4_kyo20190214b.mes": "6bf7c999ab837568","dc4_kyo20190214c.mes": "857293d0a3db2509","dc4_kyo20190214d.mes": "ca5286f0da37a4e5","dc4_mia20190301a.mes": "b59ce92f7be94170","dc4_mia20190301b.mes": "354a77ca3b1a94dd","dc4_mia20190301c.mes": "ca1d389ae657e10e","dc4_mia20190302a.mes": "9d01db412726c470","dc4_mia20190302b.mes": "4953174d42cdf265","dc4_mia20190303b.mes": "a1c67ba7fd058ccc","dc4_mia20190303c.mes": "f9275ca23d5414ae","dc4_mia20190304a.mes": "e392ce6ea0bfc45d","dc4_mia20190304c.mes": "7bf2d814d323ff35","dc4_mia20190304d.mes": "4998643f9541d7b8","dc4_mia20190305a.mes": "706e25dcb509f40d","dc4_mia20190305c.mes": "43fa22e542de9e9e","dc4_mia20190305e.mes": "d70b1f95e98ae786","dc4_mia20190306c.mes": "8d0d38f4f6b9dd4a","dc4_mia20190307d.mes": "bc406a5b827ce544","dc4_mia20190307e.mes": "c725e8911d27c802","dc4_mia20190308c.mes": "5110904f93bb8a79","dc4_mia20190308e.mes": "96c59126d59ce317","dc4_mia20190309b.mes": "393350ce12846e75","dc4_mia20190309c.mes": "aefc4cdcbc0e379c","dc4_mia20190309d.mes": "adfe3c782ba72f4b","dc4_mia20190310b.mes": "2469082f8bb3d1c3","dc4_mia20190311c.mes": "b97b1ad5cb50f1e7","dc4_mia20190312c.mes": "ee885030bd930124","dc4_mia20190313c.mes": "079c51e7d3b663fb","dc4_mia20190314b.mes": "f64cb9effd60be38","dc4_mia20190315b.mes": "5c785d9f23b21bcf","dc4_mia20190315c.mes": "84ca1bec68570e76","dc4_mia20190315e.mes": "7a9ba42506e2afa3","dc4_mib20190301a.mes": "3a44359263ba9f3d","dc4_mib20190301c.mes": "a8df8d2b73f5f847","dc4_mib20190303b.mes": "a7b094702331a11c","dc4_mib20190304c.mes": "ba01bea357bbb53d","dc4_mib20190305b.mes": "c76aecc18247b86a","dc4_mib20190306c.mes": "96d953392d7d1675","dc4_mib20190307b.mes": "73383301131b6cea","dc4_mib20190308c.mes": "dc0f96c47ad8dcc1","dc4_mib20190309b.mes": "26fad675dbd2a3d4","dc4_mib20190310b.mes": "3eb3e6378d52b8e5","dc4_mib20190311b.mes": "a9f1b3bb64aa5df9","dc4_mib20190312c.mes": "7e6c2b7b80ba518f","dc4_mib20190313c.mes": "e4102a35003e095c","dc4_mib20190314c.mes": "56d8d1537bbc12ed","dc4_mib20190314d.mes": "f87e888cda7b4d54","dc4_mib20190315b.mes": "7aa7a4b5c3c0d832","dc4_mib20190315c.mes": "065b93414767fc8b","dc4_mib20190315d.mes": "d7570c42672f2d0a","dc4_mic20190301a.mes": "fbf6715d0f24346e","dc4_mic20190301b.mes": "de96c389085d43b7","dc4_mic20190301c.mes": "a17b3d1bec44201b","dc4_mic20190302c.mes": "7a0cdd0b69af4063","dc4_mic20190304b.mes": "7b20df40fe034f3b","dc4_mic20190304c.mes": "da3af56815662019","dc4_mic20190305b.mes": "6b1d77080571b240","dc4_mic20190306c.mes": "303309aa7463a4ac","dc4_mic20190307a.mes": "5589c7cafccbec62","dc4_mic20190307c.mes": "f6725ff4452a590f","dc4_mic20190308d.mes": "7f377f026d6c2573","dc4_mic20190309b.mes": "54e4e49aa9fd9fa9","dc4_mic20190310b.mes": "279e1d7b23a2c9c4","dc4_mic20190310d.mes": "3d409e354265663f","dc4_mic20190311c.mes": "b8118c412dfbc7a6","dc4_mic20190312d.mes": "eb7ad619682c7001","dc4_mic20190313b.mes": "dcb146ec463f45f4","dc4_mic20190314c.mes": "63c66c5f377989dc","dc4_mic20190315b.mes": "1d0fba229389e8a4","dc4_mic20190315c.mes": "75659dbb80a1ad89","dc4_mic20190315d.mes": "9bc171c66150e820","dc4_mid20190301a1.mes": "70ebfef3c9e20002","dc4_mid20190301a2.mes": "b030fe0f3ea0bd84","dc4_mid20190301b.mes": "00b8c2a946e85b38","dc4_mid20190301c.mes": "ce20537712adfbd0","dc4_mid20190302a.mes": "0b9949c7293ef1b4","dc4_mid20190303b.mes": "73b7b985a1d19ff1","dc4_mid20190303c.mes": "357cd4651bebe0c2","dc4_mid20190304a.mes": "368e7e3bab24f73c","dc4_mid20190304c.mes": "f6970ecd70c7cb6b","dc4_mid20190304d.mes": "a79e0dd20860296a","dc4_mid20190305c.mes": "3d7da4c5e8084436","dc4_mid20190306c.mes": "2cfbbb8cada04fde","dc4_mid20190307c.mes": "6a4ef57c6671c7e7","dc4_mid20190307d.mes": "683c54264466b897","dc4_mid20190308c.mes": "a3565cd1d273a908","dc4_mid20190308e.mes": "abd33f88454da402","dc4_mid20190309b.mes": "d3970e1fdda6984b","dc4_mid20190309c.mes": "12f1e46961bbdb5c","dc4_mid20190310a.mes": "00b7ccecc87c050a","dc4_mid20190310b.mes": "34c296046f683a93","dc4_mid20190310d.mes": "59d3ab64ec2097a7","dc4_mid20190310e.mes": "fe38c629761c1972","dc4_mid20190311a.mes": "3fc5ea9c22e11ba1","dc4_mid20190312c.mes": "bd5efd7e37375821","dc4_mid20190314a.mes": "0117a79f610e34b3","dc4_mid20190314c.mes": "5a20aa36670f4f6c","dc4_mid20190315b.mes": "09d1c5c942dd7a13","dc4_mid20190317b.mes": "beb5d4cd64b46288","dc4_mid20190321b.mes": "9c238ab5033de823","dc4_mid20190322e.mes": "db7ff9d8ea36135c","dc4_mid20190323a.mes": "a5379a9bb565ef5c","dc4_mid20190323b.mes": "2d2abaa395821e71","dc4_mid20190324b.mes": "dd69679fd62b2aa6","dc4_mid20190326c.mes": "485c44a9a2f8ee5c","dc4_mid20190329b.mes": "f3f2a2f0537ba1b7","dc4_mid20190330a.mes": "049a74fa0e80606c","dc4_mid20190330b.mes": "1fc59afd29753555","dc4_mid20190402b.mes": "f3644ca6c1f8fdaf","dc4_mid20190402e.mes": "426088a9b911d655","dc4_mid20190403b.mes": "96ac157a9b5a21ca","dc4_mid20190404b.mes": "a7029f8f0382d60b","dc4_mid20190405e.mes": "df4887131a6266c3","dc4_mid20190406e.mes": "73d75eac8d4d3d59","dc4_mid20190407b.mes": "a73f616e6c5475af","dc4_mid20190408a.mes": "491451a6fb338027","dc4_mid20190408c.mes": "3efecacc4376cab9","dc4_mid20190409c.mes": "a0b049ae19ab6ddd","dc4_mid20190410b.mes": "b890e85129bd17a2","dc4_mid20190410c.mes": "91515e76195e4813","dc4_mid20190413b.mes": "6947dcc01af44ac7","dc4_mid20190413e.mes": "22f5f81ad61ff5d4","dc4_mid20190414b.mes": "4210833830370f3d","dc4_mid20190414e.mes": "e559b76a7662030c","dc4_mid20190415c.mes": "441056f6c3ddc966","dc4_mid20190415e.mes": "a21fd6dcf0872701","dc4_mid20190416a.mes": "ab7c3208260de353","dc4_mid20190416c.mes": "debacf1f95515e00","dc4_mid20190417c.mes": "ff49de8d20bde78c","dc4_mid20190419c.mes": "219a1a54f9e73291","dc4_mid20190420e.mes": "d2e9cbfdd9a92ccc","dc4_mid20190421a.mes": "3b18c77fb79620e9","dc4_mid20190428b.mes": "a816d786c8925548","dc4_miu20190315d.mes": "042965f085983e0f","dc4_miu20190316c.mes": "d1628f1dc8346bca","dc4_miu20190317a.mes": "7bf9a021d661b0b4","dc4_miu20190317b.mes": "4fea60b1053caa03","dc4_miu20190318b.mes": "89e60c98456bb856","dc4_miu20190319c.mes": "18e830082ac8399d","dc4_miu20190321b.mes": "820e07795ada0924","dc4_miu20190322c.mes": "13e3c73cfca99722","dc4_miu20190323b.mes": "56a992e943f7d34b","dc4_miu20190325b.mes": "3554287b5eca96fb","dc4_miu20190326b.mes": "d7e6a388bbb3689d","dc4_miu20190327c.mes": "427929039e0b449e","dc4_miu20190328b.mes": "92a633d24ca184ed","dc4_miu20190329b.mes": "be47659da0b5093b","dc4_miu20190330b.mes": "fd3b2552019f6cb2","dc4_miu20190330c.mes": "17ce6b0113eb371e","dc4_miu20190331c.mes": "359207a36229b35c","dc4_miu20190331c2.mes": "bbfa2676e1cb041a","dc4_miu20190426c.mes": "6d4e4a4cc0c110df","dc4_miu20190427c.mes": "c82722e672a2bc3b","dc4_nin20190316a.mes": "8a1b4b588bc5d567","dc4_nin20190316b.mes": "bc694440d031146c","dc4_nin20190318a.mes": "2c688b43df942af4","dc4_nin20190319b.mes": "dccdd3fed4932df6","dc4_nin20190321b.mes": "5f04fe8f4b35a44a","dc4_nin20190323b.mes": "52f118b76c93263d","dc4_nin20190324b.mes": "7457901e437d6996","dc4_nin20190324c.mes": "05b139a344a62ad5","dc4_nin20190325b.mes": "f53fe5d4d0845fee","dc4_nin20190326b.mes": "9e35a96fd90d64f8","dc4_nin20190327b.mes": "2adaaa9db71f54d8","dc4_nin20190329d.mes": "d80dfdf9bab90214","dc4_nin20190330a.mes": "d120973e840de10b","dc4_nin20190330b.mes": "53e95bb9bbf154d8","dc4_nin20190331b.mes": "0c10a6dd3562a044","dc4_nin20190401b.mes": "26768d9feed60a7c","dc4_nin20190402b.mes": "681e9887b6bbd188","dc4_nin20190408a.mes": "b155da486527b6a6","dc4_nin20190408c.mes": "6c7d093dc554d7ff","dc4_nin20190408d.mes": "e369e45eea410119","dc4_nin20190409a.mes": "4e534f67b0d064e0","dc4_nin20190409c.mes": "44d00b3ad2a520b4","dc4_nin20190409d.mes": "3e76a127e5fd2d9f","dc4_nin20190410a.mes": "a3d9b7c52fd218b9","dc4_nin20190410c.mes": "38961311c6578f5d","dc4_nin20190411a.mes": "014fe8c36dacec44","dc4_nin20190411b.mes": "5730c2439baf230f","dc4_nin20190412b.mes": "3e8cfb1469416865","dc4_nin20190412c.mes": "57cd0005ae000081","dc4_nin20190413c.mes": "fb20a2a990628ce4","dc4_nin20190414b.mes": "66be7e230d17b033","dc4_nin20190414c.mes": "6b2f62dbe0f7a3fa","dc4_nin20190415a.mes": "63959cdbe166f3d4","dc4_nin20190415c.mes": "608c84effbaa65ac","dc4_nin20190416a.mes": "1c187771cf8962de","dc4_nin20190416d.mes": "a9b81f758b2b5abd","dc4_nin20190418c.mes": "b2cfd08d8225e937","dc4_nin20190420b.mes": "7b4143cfb2085c08","dc4_nin20190421b.mes": "428935943b9b1896","dc4_nin20190421c.mes": "e1d28ec1eb3213c3","dc4_nin20190422a.mes": "6828682824643730","dc4_nin20190422d.mes": "28fec81cc101733a","dc4_nin20190423a.mes": "53adb4658ac73bd5","dc4_nin20190424a.mes": "2b27cfc31157bdcd","dc4_nin20190424d.mes": "68bcca6c2e336661","dc4_nin20190425b.mes": "fc11478625375e89","dc4_nin20190425d.mes": "fc405cd9e362f2ae","dc4_nin20190426b.mes": "0188b3ad5f08cbc4","dc4_nin20190427a.mes": "bf37e6af7fb261bd","dc4_nin20190427d.mes": "b8ed7557670e957e","dc4_nin20190428b.mes": "a213dd67df028947","dc4_nin20190429a.mes": "6b3ec73009f745a1","dc4_nin20190430c.mes": "2412a78c9da4b47e","dc4_nin20190501a.mes": "8bc724aeb9bc2189","dc4_nin20190501c.mes": "00ae26b36710e3d7","dc4_nin20190501d1.mes": "8593360700d42af9","dc4_nin20190501d2.mes": "5ea74150010ad396","dc4_nin20190501d3.mes": "30b73cb58c9ebfe6","dc4_nin20190503b.mes": "d0e0a79b25ddb95b","dc4_nin20190503d.mes": "0c5f71c7c3ee4865","dc4_nin20190511b.mes": "fc4899c481121769","dc4_nin20190511c.mes": "524574b725263e6c","dc4_sen20181213b.mes": "50fa75160e46bd81","dc4_sen20181213c.mes": "b02755391374fb8e","dc4_sen20181213d.mes": "3f3c2fceda2fd28a","dc4_sen20181214a1.mes": "41864f3bc2ef6e8e","dc4_sen20181214a2.mes": "d0f8076c33105fcc","dc4_sen20181214b.mes": "538a04eab73d6611","dc4_sen20181214d.mes": "001ab9a962354ca2","dc4_sen20181215b.mes": "cdd01ef7b14ce9ab","dc4_sen20181215d.mes": "f8ac54f925241a57","dc4_sen20181216b.mes": "14f8976ea6279561","dc4_sen20181217a.mes": "a6197f517120ed10","dc4_sen20181217b.mes": "4ce84abd299a96bb","dc4_sen20181217c.mes": "0caf37edf06e21eb","dc4_sen20181217e.mes": "eda41484a56de51b","dc4_sen20181218b.mes": "1cac4f04034b95c6","dc4_sen20181218c.mes": "eb6eecd0bacf1fc1","dc4_sen20181219b.mes": "5f406c84c8ec0f4c","dc4_sen20181219c.mes": "1a9b42ad9a4b12e4","dc4_sen20181220b.mes": "13b27a506d8850f8","dc4_sen20181220d.mes": "4dbfc8c01b18b03d","dc4_sen20181221a.mes": "a05c8e762d885555","dc4_sen20181221b.mes": "7c299dcabbfdb608","dc4_sen20181221c.mes": "00e46ef2cc384609","dc4_sen20181222b.mes": "458262354b37e609","dc4_sen20181223c.mes": "ca9d432876a88138","dc4_sen20181223d.mes": "29db878fcd531167","dc4_sen20181224b.mes": "2417c9c319bd2d5f","dc4_sen20181224c1_m0.mes": "9842d140d483823a","dc4_sen20181224c1_m1.mes": "2c1fee6b5f243557","dc4_sen20181224c1_m2.mes": "202fab89bc8caaf6","dc4_sen20181224c1_m3.mes": "c52b3236f892cb04","dc4_sen20181224c1_m4.mes": "6d30f99c6fe3785d","dc4_sen20181224c1_m5.mes": "ae8346914903f530","dc4_sen20181224c2.mes": "7e3db6d84aacf8c6","dc4_sen20181224d.mes": "b9c522802001e71e","dc4_sen20181225a.mes": "5b30e0b346fd7e50","dc4_sii20190316a.mes": "db6d5c9c9c9c5f01","dc4_sii20190316b.mes": "983b2dbd4a63ab9f","dc4_sii20190318b.mes": "deecf48a25c4a043","dc4_sii20190319c.mes": "6ad2760756d395e6","dc4_sii20190321b.mes": "58f9232f397cff49","dc4_sii20190322c.mes": "f987aeba43a20b94","dc4_sii20190323b.mes": "7770aa661b20e57e","dc4_sii20190325b.mes": "a86a6243b1f55b84","dc4_sii20190328b.mes": "cea61036ac673f8a","dc4_sii20190329d.mes": "db4b980119e98bbc","dc4_sii20190330b.mes": "1b53e3403cd4e1bb","dc4_sii20190331b.mes": "55b821e9945358a7","dc4_sii20190402c.mes": "26d37633312531ea","dc4_sii20190404c.mes": "5365c6fd28ffe0fa","dc4_sii20190405c.mes": "ee4d4aef885fedac","dc4_sii20190407a.mes": "6a768c66d659ba48","dc4_sii20190407b.mes": "fc7bbf386412505d","dc4_sii20190408d.mes": "6754563c859cdee5","dc4_sii20190409c.mes": "6c750befe52bb004","dc4_sii20190411b.mes": "4ed8ca3a265f92cc","dc4_sii20190411c.mes": "a6987be404e2bcdd","dc4_sii20190412c.mes": "d2845b5e011e8845","dc4_sii20190415c.mes": "fc056d5eddc2066a","dc4_sii20190416a.mes": "3b02cffa7553df45","dc4_sii20190416b.mes": "baf21815d6a20cee","dc4_sii20190418b.mes": "28c2b93e63d39834","dc4_sii20190418c.mes": "a646b305b1d5b595","dc4_sii20190420d.mes": "30ae4614ea1d0557","dc4_sii20190421b.mes": "674977afa2afd61b","dc4_sii20190422c.mes": "c707d169b66a3347","dc4_sii20190424c.mes": "414eb978a1cedf28","dc4_sii20190427c.mes": "6df5cb75ca62b1e2","dc4_sii20190428c.mes": "5144093fac6b7db4","dc4_sii20190501c.mes": "54a879116eec8e80","dc4_sii20190502d.mes": "e17678368f2ee0f2","dc4_sii20190503d.mes": "59bbed2591f8eccf","dc4_sii20190504b.mes": "d3b6902f12551dca","dc4_sii20190505d.mes": "4544ec712524c225","dc4_sii20190507c.mes": "bb3cf6d8e395658a","dc4_sii20190507c2.mes": "5b3f3a1e0d4ceeb6","dc4_sii20190526b.mes": "7b3fd2b38bbfd6e1","dc4_sii20190527c.mes": "ed18b3d99b74b55f","dc4_sor20190316a.mes": "8834277454e32d0f","dc4_sor20190316b.mes": "47d062b508330ca9","dc4_sor20190317b.mes": "f551d0f156e1b69e","dc4_sor20190318d.mes": "10df03753c19a1d8","dc4_sor20190319c.mes": "a0fc0fa93c26ef74","dc4_sor20190320a.mes": "f5cdc46d7fa1baf7","dc4_sor20190321b.mes": "04140581e1a8f44e","dc4_sor20190322b.mes": "af4e9d21e5587f3a","dc4_sor20190323a.mes": "e42f8999eb891f1d","dc4_sor20190323c.mes": "5b54a8cd861a0c21","dc4_sor20190323d.mes": "9c86519d37a18421","dc4_sor20190324a.mes": "98b46803058287de","dc4_sor20190324b.mes": "0c77af780339ecb8","dc4_sor20190325b.mes": "77de2d88a03a5537","dc4_sor20190326b.mes": "fec1d0c867b3a9b6","dc4_sor20190328b.mes": "82022133c071d2c4","dc4_sor20190331b.mes": "b42239a375ef741b","dc4_sor20190403b.mes": "5de6981350a31fd3","dc4_sor20190406b.mes": "88d89b95fd423070","dc4_sor20190407c.mes": "e5a4b04c1f51dc90","dc4_sor20190408b.mes": "c2b22d2bb5868ad5","dc4_sor20190408c.mes": "d95f70dd7a1f49ee","dc4_sor20190409c.mes": "36e287efa0635897","dc4_sor20190409d.mes": "d0d240df9a87976f","dc4_sor20190411c.mes": "ac075ffbba1dd27b","dc4_sor20190412a.mes": "02ace513173801b3","dc4_sor20190413b.mes": "12cd164b9ca8f626","dc4_sor20190415c.mes": "826d8022741c5c1f","dc4_sor20190418b.mes": "7548fdf53cee0c8e","dc4_sor20190419c.mes": "f2798f6680d67884","dc4_sor20190420b.mes": "42538252b52350ff","dc4_sor20190420e.mes": "ebeda87282952869","dc4_sor20190421a.mes": "cc281e48373705ea","dc4_sor20190421c.mes": "e0690150c3adfe2b","dc4_sor20190422c.mes": "745db9f9fdd91c64","dc4_sor20190423a.mes": "ab4de1591e926ac1","dc4_sor20190423c.mes": "0bc8eb2d6b33409d","dc4_sor20190424a.mes": "d5b83c215931913a","dc4_sor20190425c.mes": "7e44f3b804f098f2","dc4_sor20190427b.mes": "e6df1db4b3e011cb","dc4_sor20190430b.mes": "c0062dd19e0498fb","dc4_sor20190430c.mes": "8d52fce454e63422","dc4_sor20190430d.mes": "c5ac70a42eabc576","dc4_sor20190501a.mes": "cf6a8a13d3456be8","dc4_sor20190504a.mes": "41d8eb73eefca553","dc4_sor20190504b.mes": "49c7a4d6b49dca4b","dc4_sor20190504c.mes": "0b78290136b3840e","dc4_sor20190510c.mes": "a034ef0f04ceb4e9","dc4_sor20190511c.mes": "7d3b45d6a9e1d1a2","dc4_tiy20190316b.mes": "bfe4a64af40b3b7d","dc4_tiy20190317b.mes": "8575c715aa405b03","dc4_tiy20190320c.mes": "b4faddb178964c20","dc4_tiy20190321d.mes": "d82c79ed9a1376b9","dc4_tiy20190322d.mes": "24061be702212550","dc4_tiy20190323b.mes": "6356bc33d5245697","dc4_tiy20190324b.mes": "2c6b82916adcac34","dc4_tiy20190326b.mes": "dc44b5f45f373d3c","dc4_tiy20190327c.mes": "ba154980313c40dc","dc4_tiy20190329c.mes": "ad43516126ed0b9d","dc4_tiy20190329d.mes": "969e131520532809","dc4_tiy20190330b.mes": "81575a226f66f8e3","dc4_tiy20190331b.mes": "e5107b33aeb0fdc8","dc4_tiy20190401c.mes": "ae71e91dd03bb753","dc4_tiy20190402c.mes": "fbd84135eafa8c0d","dc4_tiy20190403b.mes": "038559008f73b18e","dc4_tiy20190404c.mes": "6588745bdf0aa562","dc4_tiy20190405d.mes": "04a7ce99cf23e880","dc4_tiy20190405d2.mes": "d5109a3af206606e","dc4_tiy20190405d2_bk.mes": "a262c4add6cf3f6f","dc4_tiy20190426d1.mes": "ab6686ccbb90fb5c","dc4_tiy20190426d2.mes": "cf76d9c6ecd86f01","sce_asa.mes": "7c58711f6f65f822","sce_com.mes": "3880594bd2b70aff","sce_hiy.mes": "1b77712e634e647d","sce_miu.mes": "3bce30ecc9dfa252","sce_nin.mes": "796c28608c8a64e2","sce_sii.mes": "a518e49be871ad1b","sce_sor.mes": "f21c9c88ffec4ffc","sce_tiy.mes": "2dbb85690081885f"}''')
FONT_FAMILY = 'DC4TC'
EXE = 'DC4PHDL.exe'
STORE = 'DC4PH_CHT'

# ---------------------------------------------------------------- Circus MES (dc4ph)
U8X2 = (0x00, 0x3A); U8STR = (0x3B, 0x47); STR = (0x48, 0x68); ENC = (0x69, 0x6D); U16X4 = (0x6E, 0xFF)
KEY = 0x20; OPSTRS = (0x5D,)
def _in(r, v): return r[0] <= v <= r[1]

def mes_tokens(d):
    n = struct.unpack_from('<i', d, 0)[0]
    p = n * 6 + 4 + 3
    toks = []
    while p < len(d):
        op = d[p]
        if _in(U8X2, op): L = 3
        elif _in(U8STR, op): L = d.index(b'\x00', p + 2) + 1 - p
        elif _in(STR, op) or _in(ENC, op): L = d.index(b'\x00', p + 1) + 1 - p
        elif _in(U16X4, op): L = 9
        else: raise ValueError('bad opcode %02X at %X' % (op, p))
        toks.append((p, op, L)); p += L
    if p != len(d): raise ValueError('token overrun')
    return toks

def mes_texts(d):
    for p, op, L in mes_tokens(d):
        if _in(ENC, op): yield p + 1, p + L - 1, True
        elif op in OPSTRS: yield p + 1, p + L - 1, False

def payload(d, s, e, enc):
    b = d[s:e]
    return bytes((x + KEY) & 0xFF for x in b) if enc else b

# ---------------------------------------------------------------- helpers
KANA = re.compile('[ぁ-ゖゝ-ゟァ-ヺヽ-ヿ]')
WS = '\n\u3000 '

def protected(sc):
    keep = set()
    for i, c in enumerate(sc):
        if c == '栖': keep.add(i)                                   # 有里栖
        elif c == '里' and i > 0 and sc[i-1] in '有琴': keep.add(i)  # 有里咲 / 有里栖 / 琴里
        elif c == '叶':                                             # 叶方 (Kanata)
            j = i + 1
            while j < len(sc) and sc[j] in WS: j += 1
            if j < len(sc) and sc[j] == '方': keep.add(i)
    return keep

def safe_cp932(ch):
    try: b = ch.encode('cp932')
    except UnicodeEncodeError: return None
    if len(b) == 2 and b[0] > 0xEE: return None
    return b

def convert_scripts(sc_dir, files, sc_map):
    from opencc import OpenCC
    cc = OpenCC('s2tw')
    pua2sc = {v: k for k, v in sc_map.items()}
    unpua = lambda s: ''.join(pua2sc.get(ord(c), c) for c in s)
    jobs, need = [], collections.Counter()
    for k, fn in enumerate(files, 1):
        if k % 100 == 0: say('   ... %d / %d' % (k, len(files)))
        d = rd(os.path.join(sc_dir, fn))
        items = []
        for s, e, enc in mes_texts(d):
            raw = payload(d, s, e, enc)
            u = raw.decode('cp932')
            sc = unpua(u)
            if KANA.search(sc) and not any(0xE000 <= ord(c) <= 0xF8FF for c in u):
                continue                         # untranslated Japanese line
            tc = cc.convert(sc)
            if len(tc) != len(sc): tc = ''.join(cc.convert(c) for c in sc)
            keep = protected(sc)
            if keep: tc = ''.join(sc[i] if i in keep else c for i, c in enumerate(tc))
            for c in tc:
                if safe_cp932(c) is None: need[c] += 1
            items.append((s, e, enc, raw, sc, tc))
        jobs.append((fn, d, items))
    order, seen = [], set()
    for fn, d, items in jobs:
        for *_, tc in items:
            for c in tc:
                if c in need and c not in seen: seen.add(c); order.append(c)
    if len(order) > 0xE757 - 0xE000 + 1: raise RuntimeError('too many characters for the PUA carrier area')
    tc_map = {c: 0xE000 + i for i, c in enumerate(order)}
    def enc_char(c):
        b = safe_cp932(c)
        return b if b is not None else chr(tc_map[c]).encode('cp932')
    out_files, used = {}, collections.Counter()
    inv = {v: k for k, v in tc_map.items()}
    for fn, d, items in jobs:
        buf = bytearray(d)
        for s, e, enc, raw, sc, tc in items:
            out = bytearray(); pos = 0
            for a, b in zip(sc, tc):
                w = 1 if raw[pos] < 0x80 or 0xA1 <= raw[pos] <= 0xDF else 2
                src = raw[pos:pos + w]; pos += w
                if a == b and not (w == 2 and 0xF0 <= src[0] <= 0xF9): out += src
                else:
                    nb = enc_char(b)
                    if len(nb) != w: raise RuntimeError('width mismatch in %s' % fn)
                    out += nb
            if enc:
                out = bytes((x - KEY) & 0xFF for x in out)
                if 0 in out: raise RuntimeError('NUL in encrypted text in %s' % fn)
            buf[s:e] = out
        buf = bytes(buf)
        if [t[:2] for t in mes_tokens(buf)] != [t[:2] for t in mes_tokens(d)]: raise RuntimeError('layout changed in %s' % fn)
        out_files[fn] = buf
        for s, e, enc in mes_texts(buf):
            used.update(inv.get(ord(c), c) for c in payload(buf, s, e, enc).decode('cp932'))
    return out_files, tc_map, used

# ---------------------------------------------------------------- step: font
def build_font(src_path, note_path, tc_map, used, out_path):
    from fontTools.ttLib import TTFont
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.transformPen import TransformPen
    f = TTFont(src_path, fontNumber=0)
    EM = f['head'].unitsPerEm
    ASC = round(EM * 0.88); DESC = EM - ASC; MID = (ASC - DESC) / 2
    glyf, hmtx = f['glyf'], f['hmtx']
    vmtx = f['vmtx'] if 'vmtx' in f else None
    cmap = f.getBestCmap(); order = f.getGlyphOrder()

    def add(name, g, adv, lsb=None):
        g.recalcBounds(glyf)
        if lsb is None: lsb = getattr(g, 'xMin', 0) if g.numberOfContours else 0
        order.append(name); glyf.glyphs[name] = g
        if hasattr(glyf, 'glyphOrder'): glyf.glyphOrder = order
        hmtx.metrics[name] = (adv, lsb)
        if vmtx is not None:
            top = getattr(g, 'yMax', ASC) if g.numberOfContours else ASC
            vmtx.metrics[name] = (EM, max(0, ASC - top))
        return name

    def outline(gs, gname, dx=0, dy=0, scale=1.0, per=None):
        rec = DecomposingRecordingPen(gs); gs[gname].draw(rec)
        pen = TTGlyphPen(None)
        if per is None:
            rec.replay(TransformPen(pen, (scale, 0, 0, scale, dx, dy)))
        else:
            ci = 0; tp = TransformPen(pen, (scale, 0, 0, scale, dx + per[0], dy))
            for op, args in rec.value:
                getattr(tp, op)(*args)
                if op in ('closePath', 'endPath'):
                    ci += 1
                    if ci < len(per): tp = TransformPen(pen, (scale, 0, 0, scale, dx + per[ci], dy))
        return pen.glyph()

    gs = f.getGlyphSet(); override = {}
    sd = glyf[cmap[0x2014]]; sd.recalcBounds(glyf); th = sd.yMax - sd.yMin
    pen = TTGlyphPen(None); y0, y1 = round(MID - th / 2), round(MID + th / 2)
    pen.moveTo((0, y0)); pen.lineTo((0, y1)); pen.lineTo((EM, y1)); pen.lineTo((EM, y0)); pen.closePath()
    override[0x2014] = override[0x2015] = add('dc4.dash.fw', pen.glyph(), EM, 0)

    eg = glyf[cmap[0x2026]]; eg.recalcBounds(glyf)
    coords, ends, _ = eg.getCoordinates(glyf)
    starts = [0] + [e + 1 for e in ends[:-1]]
    centres = [(min(coords[i][0] for i in range(s, e + 1)) + max(coords[i][0] for i in range(s, e + 1))) / 2 for s, e in zip(starts, ends)]
    targets = [EM * (2 * i + 1) / (2 * len(centres)) for i in range(len(centres))]
    override[0x2026] = add('dc4.ellipsis.fw', outline(gs, cmap[0x2026], dy=round(MID - (eg.yMin + eg.yMax) / 2),
                           per=[round(t - c) for t, c in zip(targets, centres)]), EM)

    if 0x266A not in cmap and note_path:
        nf = TTFont(note_path, fontNumber=0); ncm = nf.getBestCmap()
        if 0x266A in ncm:
            k = EM / nf['head'].unitsPerEm; adv = nf['hmtx'][ncm[0x266A]][0] * k
            override[0x266A] = add('dc4.musicnote', outline(nf.getGlyphSet(), ncm[0x266A], scale=k, dx=round((EM - adv) / 2)), EM)

    pua_set = set(tc_map.values())
    def dbcs(ch):
        if ord(ch) in (0xA5, 0x203E): return False
        if ch in tc_map or ord(ch) in pua_set: return True
        try: return len(ch.encode('cp932')) == 2
        except UnicodeEncodeError: return True
    for ch in used:
        cp = ord(ch)
        if cp < 0x80 or cp in override or cp not in cmap or not dbcs(ch) or 0xFF61 <= cp <= 0xFF9F: continue
        if hmtx[cmap[cp]][0] != EM:
            adv = hmtx[cmap[cp]][0]
            override[cp] = add('dc4.fw.%04X' % cp, outline(gs, cmap[cp], dx=round((EM - adv) / 2)), EM)

    missing = set()
    for t in f['cmap'].tables:
        if not t.isUnicode(): continue
        for cp, g in override.items(): t.cmap[cp] = g
        for ch, pua in tc_map.items():
            g = override.get(ord(ch)) or cmap.get(ord(ch))
            if g is None: missing.add(ch); continue
            t.cmap[pua] = g
    if missing: say('   note: %d characters not in the font: %s' % (len(missing), ''.join(sorted(missing))))
    f.setGlyphOrder(order); f['maxp'].numGlyphs = len(order)
    if hasattr(f['post'], 'extraNames'): f['post'].formatType = 3.0
    for t in ('hdmx', 'LTSH', 'VDMX', 'MERG', 'DSIG', 'kern'):
        if t in f: del f[t]
    hh, os2 = f['hhea'], f['OS/2']
    hh.ascent, hh.descent, hh.lineGap = ASC, -DESC, 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ASC, -DESC, 0
    os2.usWinAscent, os2.usWinDescent = ASC, DESC
    if 'vhea' in f: f['vhea'].ascent, f['vhea'].descent = EM // 2, -(EM // 2)
    os2.ulCodePageRange1 = (os2.ulCodePageRange1 | (1 << 17)) & ~(1 << 18)
    name = f['name']
    name.names = [n for n in name.names if n.nameID not in (1, 2, 3, 4, 6, 16, 17, 18, 21, 22)]
    for nid, val in ((1, FONT_FAMILY), (2, 'Regular'), (3, FONT_FAMILY + ';DC4PH-CHT'), (4, FONT_FAMILY), (6, FONT_FAMILY)):
        name.setName(val, nid, 3, 1, 0x409)
    f['head'].fontRevision = 1.0
    os2.usWeightClass = 400
    os2.fsSelection = (os2.fsSelection & ~((1 << 5) | 1)) | (1 << 6)
    f['head'].macStyle &= ~0b11
    os2.fsType = 0
    f.save(out_path)


# ---------------------------------------------------------------- text size
def size_keys(size):
    # FontHook's own height scaling stays off: the engine draws at EngineFontSize itself.
    # (The old +5% FontHook scaling squeezed glyphs into fixed cells - see ph_textfix.py.)
    return [('EnableFontHeightScale', '0'), ('FontHeightScale1000', '1000'), ('EngineFontSize', str(size))]


def size_inis():
    cands = ('FontHook.ini', os.path.join(STORE, 'CHT', 'FontHook.ini'), os.path.join(STORE, 'SC_backup', 'FontHook.ini'))
    return [p for p in cands if os.path.exists(p)]


def current_size():
    v = ini_get(ini_read('FontHook.ini')[1], 'EngineFontSize')
    return int(v) if v and v.isdigit() else None


def set_size(size):
    """Change the text size only. The game reads EngineFontSize every time it starts."""
    for p in size_inis():
        ini_update(p, tail=size_keys(size))
    return size_inis()


def is_installed():
    need = [os.path.join(STORE, 'CHT', 'DC4CN.ttf'), os.path.join(STORE, 'CHT', 'FontHook.ini'),
            os.path.join(STORE, 'SC_backup', 'FontHook.ini'), os.path.join(STORE, 'DC4PHDL.exe.original')]
    return all(os.path.exists(p) for p in need) and b'.patch\x00\x00' in rd(EXE)[:4096]


def sc_patch_present():
    """The acies Simplified patch is installed (or already backed up by this tool)."""
    if os.path.exists(os.path.join(STORE, 'SC_backup', '_work', 'carrier_map.json')):
        return True
    return all(os.path.exists(p) for p in ('winmm.dll', 'FontHook.ini', 'DC4CN.ttf', os.path.join('_work', 'carrier_map.json')))


def current_language():
    return 'cht' if ini_get(ini_read('FontHook.ini')[1], 'FontNameW') == FONT_FAMILY else 'chs'


def switch_language(lang):
    """Same as the 切換/切换 .bat files: copy that language's files into the game."""
    src = os.path.join(STORE, 'CHT' if lang == 'cht' else 'SC_backup')
    mes_src = os.path.join(src, 'Advdata', 'MES')
    for fn in os.listdir(mes_src):
        wr(os.path.join('Advdata', 'MES', fn), rd(os.path.join(mes_src, fn)))
    for p in ('DC4CN.ttf', 'FontHook.ini', os.path.join('_work', 'carrier_map.json')):
        wr(p, rd(os.path.join(src, p)))
    grp = os.path.join('Advdata', 'GRP')
    for fn in os.listdir(grp) if os.path.isdir(grp) else []:
        if fn.upper().startswith('FONT') and fn.upper().endswith('.IMG'):
            os.remove(os.path.join(grp, fn))


def _getacp_only(src):
    """Fallback when the text fix does not recognise this DC4PHDL.exe build."""
    from ph_textfix import parse_pe
    pe = parse_pe(src)
    data = bytearray(src)
    n = 0
    if 'GetACP' in pe['iat']:
        pat = b'\xff\x15' + struct.pack('<I', pe['iat']['GetACP'])
        for s in pe['sections']:
            i, hi = s['raw'], s['raw'] + s['rsize']
            while True:
                i = data.find(pat, i, hi)
                if i < 0: break
                data[i:i + 6] = b'\xb8\xa4\x03\x00\x00\x90'      # mov eax, 932 ; nop
                n += 1; i += 6
    return bytes(data), n


def _bat(name, src, msg):
    lines = ['@echo off', 'cd /d "%~dp0"',
             'if not exist "%s\\DC4CN.ttf" (echo [ERROR] %s not found. & pause & exit /b 1)' % (src, src),
             'echo Close the game first.',
             'xcopy "%s\\Advdata\\*" "Advdata\\" /E /Y /I /Q' % src,
             'if errorlevel 1 (echo [ERROR] copy failed - is the game still running? & pause & exit /b 1)',
             'copy /y "%s\\DC4CN.ttf" "DC4CN.ttf" >nul' % src,
             'copy /y "%s\\FontHook.ini" "FontHook.ini" >nul' % src,
             'if not exist "_work" mkdir "_work"',
             'copy /y "%s\\_work\\carrier_map.json" "_work\\carrier_map.json" >nul' % src,
             'del /q "Advdata\\GRP\\FONT*.IMG" 2>nul', 'echo Done. %s' % msg, 'pause']
    wr(name, ('\r\n'.join(lines) + '\r\n').encode('ascii'))


# ---------------------------------------------------------------- install
def install(size, version):
    mes_dir = os.path.join('Advdata', 'MES')
    if not (os.path.exists(EXE) and os.path.isdir(mes_dir)):
        raise RuntimeError('This is not a D.C.4 Plus Harmony folder (DC4PHDL.exe / Advdata\\MES missing).')
    scb = os.path.join(STORE, 'SC_backup'); cht = os.path.join(STORE, 'CHT')

    # 1. Simplified patch source (backup on first run)
    if os.path.exists(os.path.join(scb, '_work', 'carrier_map.json')):
        say('[1/5] Using the saved Simplified Chinese backup')
        src_root = scb
    else:
        say('[1/5] Checking the Simplified Chinese patch...')
        for p in ('winmm.dll', 'FontHook.ini', 'DC4CN.ttf', os.path.join('_work', 'carrier_map.json')):
            if not os.path.exists(p):
                raise RuntimeError('The Simplified Chinese patch by acies was not found (%s is missing).\n'
                                   'Install it first (see README), then run this again.' % p)
        m = json.loads(rd(os.path.join('_work', 'carrier_map.json')).decode('utf-8'))
        if m.get('买') != 57344:
            raise RuntimeError('_work\\carrier_map.json is not from the Simplified Chinese patch.\n'
                               'If Traditional Chinese was installed by hand before, reinstall the\n'
                               'Simplified Chinese patch first, then run this again.')
        say('      backing up the Simplified files -> %s' % scb)
        for fn in sorted(os.listdir(mes_dir)):
            if fn in SC_HASHES:
                wr(os.path.join(scb, mes_dir, fn), rd(os.path.join(mes_dir, fn)))
        for p in ('DC4CN.ttf', 'FontHook.ini', os.path.join('_work', 'carrier_map.json')):
            wr(os.path.join(scb, p), rd(p))
        src_root = scb
    sc_map = json.loads(rd(os.path.join(src_root, '_work', 'carrier_map.json')).decode('utf-8'))
    src_mes = os.path.join(src_root, mes_dir)
    files = sorted(fn for fn in os.listdir(src_mes) if fn in SC_HASHES)
    if not files: raise RuntimeError('No Simplified Chinese patch scripts found in Advdata\\MES.')
    mism = [fn for fn in files if sha16(rd(os.path.join(src_mes, fn))) != SC_HASHES[fn]]
    say('      %d patch scripts found%s' % (len(files), '' if not mism else
        ' (%d differ from the tested patch version - converting anyway)' % len(mism)))

    # 2. convert
    say('[2/5] Converting the text to Traditional Chinese...')
    out, tc_map, used = convert_scripts(src_mes, files, sc_map)
    for fn in os.listdir(mes_dir):                       # count chars of untouched (Japanese) scripts too
        if fn not in out and fn.lower().endswith('.mes'):
            try:
                d = rd(os.path.join(mes_dir, fn))
                for s, e, enc in mes_texts(d): used.update(payload(d, s, e, enc).decode('cp932', 'replace'))
            except Exception: pass
    same = sum(1 for fn, b in out.items() if CHT_HASHES.get(fn) == sha16(b))
    say('      %d files converted (%d identical to the reference build), %d special characters' % (len(out), same, len(tc_map)))
    for fn, b in out.items(): wr(os.path.join(cht, mes_dir, fn), b)
    wr(os.path.join(cht, '_work', 'carrier_map.json'), json.dumps(tc_map, ensure_ascii=False, indent=0).encode('utf-8'))

    # 3. font + FontHook.ini
    say('[3/5] Building the font from Microsoft JhengHei Bold (about 1 minute)...')
    src_font = find_font('msjhbd.ttc', 'msjh.ttc')
    if not src_font: raise RuntimeError('Microsoft JhengHei (msjhbd.ttc / msjh.ttc) was not found in Windows\\Fonts.')
    note_font = find_font('YuGothR.ttc', 'YuGothM.ttc', 'msgothic.ttc', 'seguisym.ttf')
    say('      source: %s' % src_font)
    build_font(src_font, note_font, tc_map, used, os.path.join(cht, 'DC4CN.ttf'))
    bom, ini = ini_read(os.path.join(src_root, 'FontHook.ini'))
    ini_write(os.path.join(cht, 'FontHook.ini'),
              ini_set(ini, head=[('FontNameW', FONT_FAMILY), ('FontNameA', FONT_FAMILY)], tail=size_keys(size)), bom)
    ini_update(os.path.join(scb, 'FontHook.ini'), tail=size_keys(size))     # Simplified keeps the same size

    # 4. exe
    say('[4/5] Patching DC4PHDL.exe (Shift-JIS fix + text fix by hyther1111)...')
    orig = os.path.join(STORE, 'DC4PHDL.exe.original')
    if not os.path.exists(orig): wr(orig, rd(EXE))
    src = rd(orig)
    try:
        patched, acp_n, added = patch_exe_bytes(src, size)
        say('      done%s; original saved as %s' % ('' if added else ' (text fix was already in this exe)', orig))
    except RuntimeError as ex:
        patched, acp_n = _getacp_only(src)
        say('      WARNING: %s' % ex)
        say('      Only the Shift-JIS fix was applied; English letters may overlap in this game version.')
    wr(EXE, patched)

    # 5. switch scripts + apply
    say('[5/5] Installing Traditional Chinese and writing the switch scripts...')
    _bat('切換繁體中文(CHT).bat', cht, 'Traditional Chinese (CHT)')
    _bat('切换简体中文(CHS).bat', scb, 'Simplified Chinese (original patch)')
    for fn in out: wr(os.path.join(mes_dir, fn), rd(os.path.join(cht, mes_dir, fn)))
    for p in ('DC4CN.ttf', 'FontHook.ini', os.path.join('_work', 'carrier_map.json')): wr(p, rd(os.path.join(cht, p)))
    grp = os.path.join('Advdata', 'GRP')
    for fn in os.listdir(grp) if os.path.isdir(grp) else []:
        if fn.upper().startswith('FONT') and fn.upper().endswith('.IMG'): os.remove(os.path.join(grp, fn))
    wr(os.path.join(STORE, 'install.json'),
       json.dumps({'tool': 'DC4-CHT-Patch', 'version': version, 'size': size}).encode('utf-8'))

