//Maya ASCII 2016 scene
//Name: woodpecker-pkr.ma
//Last modified: Mon, Oct 05, 2015 03:09:49 PM
//Codeset: UTF-8
requires maya "2016";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2016";
fileInfo "version" "2016";
fileInfo "cutIdentifier" "201508242200-969261";
fileInfo "osv" "Linux 3.10.0-229.14.1.el7.x86_64 #1 SMP Tue Sep 15 15:05:51 UTC 2015 x86_64";
createNode geometryVarGroup -n "Woodpecker_PIKR";
	rename -uid "B04528C0-0000-5C6B-5612-C116000036A2";
	addAttr -ci true -sn "bgImage" -ln "bgImage" -dt "string";
	addAttr -ci true -sn "bgColor" -ln "bgColor" -dt "string";
	addAttr -ci true -sn "count" -ln "count" -at "long";
	addAttr -ci true -sn "data" -ln "data" -dt "stringArray";
	addAttr -ci true -sn "width" -ln "width" -dt "Int32Array";
	addAttr -ci true -sn "height" -ln "height" -dt "Int32Array";
	addAttr -ci true -sn "overlay" -ln "overlay" -dt "stringArray";
	addAttr -ci true -sn "command" -ln "command" -dt "stringArray";
	addAttr -ci true -sn "image" -ln "image" -dt "stringArray";
	addAttr -ci true -sn "label" -ln "label" -dt "stringArray";
	addAttr -ci true -sn "charPrefix" -ln "charPrefix" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "mirrorPicker" -ln "mirrorPicker" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "pickerScale" -ln "pickerScale" -at "float";
	setAttr ".bgImage" -type "string" "/home/italic/maya/pickers/img/bird.jpg";
	setAttr ".bgColor" -type "string" "0.2666666806:0.2666666806:0.2666666806::::";
	setAttr ".count" 91;
	setAttr ".data" -type "stringArray" 89 "193:154:0.7:0.7:0.4" "246:120:0.7:0.4:0.4" "233:100:0.7:0.4:0.4" "214:110:0.75:0.5:1" "176:97:0.7:0.7:0.4" "175:73:0.7:0.4:0.4" "150:12:0.7:0.4:0.4" "169:56:0.7:0.4:0.4" "259:171:0.7:0.4:0.4" "266:189:0.7:0.4:0.4" "260:213:0.7:0.7:0.4" "267:227:0:0.5:1" "252:227:1:0:0" "185:179:0.7:0.7:0.4" "225:128:0.75:0.5:1" "79:192:0:0.5:1" "48:193:1:0:0" "201:405:0:0.5:1" "220:178:0:0.5:1" "78:216:0:0.5:1" "59:216:1:0:0" "172:406:1:0:0" "156:181:1:0:0" "155:117:0.7:0.7:0.4" "280:30:0:0.5:1" "256:30:1:0:0" "280:19:0.5:0.75:1" "280:48:0.5:0.75:1" "255:19:1:0.5:0.5" "255:48:1:0.5:0.5" "227:204:0:0.5:1" "227:218:0:0.5:1" "227:232:0:0.5:1" "143:205:1:0:0" "143:219:1:0:0" "143:233:1:0:0" "208:209:0:0.5:1" "129:212:1:0:0" "169:243:0.6:0.6:0.6" "224:308:0.5:1:1" "207:308:0.5:1:1" "224:294:0.5:1:1" "207:294:0.5:1:1" "226:321:0:0.75:0.75" "229:334:0:0.75:0.75" "234:346:0:0.75:0.75" "233:281:0:0.75:0.75" "243:270:0:0.75:0.75" "203:321:0:0.75:0.75" "200:333:0:0.75:0.75" "198:345:0:0.75:0.75" "201:282:0:0.75:0.75" "194:271:0:0.75:0.75" "158:306:1:0.5:0.5" "142:306:1:0.5:0.5" "158:294:1:0.5:0.5" "142:294:1:0.5:0.5" "78:232:0:0.5:1" "52:232:1:0:0" "222:358:0:0.5:1" "208:358:0:0.5:1" "210:259:0:0.5:1" "225:259:0:0.5:1" "161:318:0.75:0:0" "165:329:0.75:0:0" "168:340:0.75:0:0" "140:318:0.75:0:0" "138:329:0.75:0:0" "136:340:0.75:0:0" "164:282:0.75:0:0" "172:271:0.75:0:0" "135:283:0.75:0:0" "125:273:0.75:0:0" "144:353:1:0:0" "158:353:1:0:0" "142:266:1:0:0" "157:266:1:0:0" "204:382:0:0.5:1" "223:386:0:0.5:1" "243:379:0:0.5:1" "288:355:0:0.5:1" "55:356:1:0:0" "172:383:1:0:0" "152:389:1:0:0" "132:380:1:0:0" "136:67:0.7:0.7:0.4" "11:11:0.8:0.8:0.8" "11:37:0.8:0.8:0.8" "11:62:0.8:0.8:0.8"  ;
	setAttr ".width" -type "Int32Array" 89 32 13 14 13 19 20
		 32 20 13 13 11 11 11 21 13 22 22 14
		 16 11 11 14 16 11 17 15 16 16 16 16
		 11 11 11 11 11 11 9 8 42 11 11 11
		 11 11 11 11 11 11 11 11 11 11 11 11
		 11 11 11 17 17 11 11 11 11 11 11 11
		 11 11 11 11 11 11 11 11 11 11 11 11
		 11 11 27 27 11 11 11 11 39 39 39 ;
	setAttr ".height" -type "Int32Array" 89 18 14 14 13 18 14
		 15 14 12 14 11 11 11 14 13 14 14 13
		 16 11 11 13 16 11 14 14 8 8 8 8
		 11 11 11 11 11 11 9 8 8 9 9 9
		 9 9 9 9 9 9 9 9 9 9 9 9
		 9 9 9 16 16 11 11 11 11 9 9 9
		 9 9 9 9 9 9 9 11 11 11 11 11
		 11 11 14 14 11 11 11 11 18 18 18 ;
	setAttr ".overlay" -type "stringArray" 89 "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""  ;
	setAttr ".command" -type "stringArray" 89 "abxPickerSelect \" woodpecker_ac_cn_upperbody\"" "abxPickerSelect \" woodpecker_ac_cn_spineFK1\"" "abxPickerSelect \" woodpecker_ac_cn_spineFK2\"" "abxPickerSelect \" woodpecker_ac_cn_spineFK2_inv\"" "abxPickerSelect \" woodpecker_ac_cn_chest\"" "abxPickerSelect \" woddpecker_ac_cn_neck_1\"" "abxPickerSelect \" woddpecker_ac_cn_head\"" "abxPickerSelect \" woddpecker_ac_cn_neck_2\"" "abxPickerSelect \" woodpecker_ac_cn_tail_1\"" "abxPickerSelect \" woodpecker_ac_cn_tail_2\"" "abxPickerSelect \" woodpecker_ac_cn_tail_settings\"" "abxPickerSelect \" woodpecker_ac_lf_tail_settings\"" "abxPickerSelect \" woodpecker_ac_rt_tail_settings\"" "abxPickerSelect \" woodpecker_ac_cn_pelvis\"" "abxPickerSelect \" woodpecker_ac_cn_spineFK1_inv\"" "abxPickerSelect \" woodpecker_ac_lf_leg_settings\"" "abxPickerSelect \" woodpecker_ac_rt_leg_settings\"" "abxPickerSelect \" woodpecker_ac_lf_clavicle\"" "abxPickerSelect \" woodpecker_ac_lf_hip\"" "abxPickerSelect \" woodpecker_ac_lf_legPole\"" "abxPickerSelect \" woodpecker_ac_rt_legPole\"" "abxPickerSelect \" woodpecker_ac_rt_clavicle\"" "abxPickerSelect \" woodpecker_ac_rt_hip\"" "abxPickerSelect \" woodpecker_ac_cn_free_chest\"" "abxPickerSelect \" woodpecker_ac_lf_eye\"" "abxPickerSelect \" woodpecker_ac_rt_eye\"" "abxPickerSelect \" woddpecker_ac_lf_up_eyelid\"" "abxPickerSelect \" woddpecker_ac_lf_low_eyelid\"" "abxPickerSelect \" woddpecker_ac_rt_up_eyelid\"" "abxPickerSelect \" woddpecker_ac_rt_low_eyelid\"" "abxPickerSelect \" woodpecker_ac_lf_kneeFK\"" "abxPickerSelect \" woodpecker_ac_lf_ankleFK\"" "abxPickerSelect \" woodpecker_ac_lf_fingerstFK\"" "abxPickerSelect \" woodpecker_ac_rt_kneeFK\"" "abxPickerSelect \" woodpecker_ac_rt_ankleFK\"" "abxPickerSelect \" woodpecker_ac_rt_fingerstFK\"" "abxPickerSelect \" woodpecker_ac_lf_kneeFK woodpecker_ac_lf_ankleFK woodpecker_ac_lf_fingerstFK\"" "abxPickerSelect \" woodpecker_ac_rt_kneeFK woodpecker_ac_rt_ankleFK woodpecker_ac_rt_fingerstFK\"" "abxPickerSelect \" woodpecker_ac_cn_base\"" "abxPickerSelect \" woodpecker_sk_lf_finger_1_1\"" "abxPickerSelect \" woodpecker_sk_lf_finger_2_1\"" "abxPickerSelect \" woodpecker_sk_lf_finger_4_1\"" "abxPickerSelect \" woodpecker_sk_lf_finger_3_1\"" "abxPickerSelect \" woodpecker_sk_lf_finger_1_2\"" "abxPickerSelect \" woodpecker_sk_lf_finger_1_3\"" "abxPickerSelect \" woodpecker_sk_lf_finger_1_4\"" "abxPickerSelect \" woodpecker_sk_lf_finger_4_2\"" "abxPickerSelect \" woodpecker_sk_lf_finger_4_3\"" "abxPickerSelect \" woodpecker_sk_lf_finger_2_2\"" "abxPickerSelect \" woodpecker_sk_lf_finger_2_3\"" "abxPickerSelect \" woodpecker_sk_lf_finger_2_4\"" "abxPickerSelect \" woodpecker_sk_lf_finger_3_2\"" "abxPickerSelect \" woodpecker_sk_lf_finger_3_3\"" "abxPickerSelect \" woodpecker_sk_rt_finger_2_1\"" "abxPickerSelect \" woodpecker_sk_rt_finger_1_1\"" "abxPickerSelect \" woodpecker_sk_rt_finger_3_1\"" "abxPickerSelect \" woodpecker_sk_rt_finger_4_1\"" "abxPickerSelect \" woodpecker_ac_lf_footIK\"" "abxPickerSelect \" woodpecker_ac_rt_footIK\"" "abxPickerSelect \" woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger2_offset|woodpecker_ac_lf_finger2\"" "abxPickerSelect \" woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger1_offset|woodpecker_ac_lf_finger1\"" "abxPickerSelect \" woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger3_offset|woodpecker_ac_lf_finger3\"" "abxPickerSelect \" woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger4_offset|woodpecker_ac_lf_finger4\"" "abxPickerSelect \" woodpecker_sk_rt_finger_2_2\"" "abxPickerSelect \" woodpecker_sk_rt_finger_2_3\"" "abxPickerSelect \" woodpecker_sk_rt_finger_2_4\"" "abxPickerSelect \" woodpecker_sk_rt_finger_1_2\"" "abxPickerSelect \" woodpecker_sk_rt_finger_1_3\"" "abxPickerSelect \" woodpecker_sk_rt_finger_1_4\"" "abxPickerSelect \" woodpecker_sk_rt_finger_3_2\"" "abxPickerSelect \" woodpecker_sk_rt_finger_3_3\"" "abxPickerSelect \" woodpecker_sk_rt_finger_4_2\"" "abxPickerSelect \" woodpecker_sk_rt_finger_4_3\"" "abxPickerSelect \" woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger2_offset|woodpecker_ac_lf_finger2\"" "abxPickerSelect \" woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger1_offset|woodpecker_ac_lf_finger1\"" "abxPickerSelect \" woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger4_offset|woodpecker_ac_lf_finger4\"" "abxPickerSelect \" woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger3_offset|woodpecker_ac_lf_finger3\"" "abxPickerSelect \" woodpecker_ac_lf_shoulder\"" "abxPickerSelect \" woodpecker_ac_lf_elbow\"" "abxPickerSelect \" woodpecker_ac_lf_wrink\"" "abxPickerSelect \" woodpecker_ac_lf_wing_settings\"" "abxPickerSelect \" woodpecker_ac_rt_wing_settings\"" "abxPickerSelect \" woodpecker_ac_rt_shoulder\"" "abxPickerSelect \" woodpecker_ac_rt_elbow\"" "abxPickerSelect \" woodpecker_ac_rt_wrink\"" "abxPickerSelect \" woodpecker_ac_cn_jaw\"" "abxPickerSelect \" woodpecker_ac_cn_upperbody woodpecker_ac_cn_spineFK2_inv woodpecker_ac_cn_spineFK1 woodpecker_ac_cn_spineFK2 woodpecker_ac_cn_spineFK1_inv woodpecker_ac_cn_chest woddpecker_ac_cn_head woddpecker_ac_cn_neck_2 woddpecker_ac_cn_neck_1 woddpecker_ac_lf_low_eyelid woddpecker_ac_lf_up_eyelid woodpecker_ac_lf_eye woddpecker_ac_rt_low_eyelid woddpecker_ac_rt_up_eyelid woodpecker_ac_rt_eye woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger2_offset|woodpecker_ac_lf_finger2 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger1_offset|woodpecker_ac_lf_finger1 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger3_offset|woodpecker_ac_lf_finger3 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger4_offset|woodpecker_ac_lf_finger4 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger3_offset|woodpecker_ac_lf_finger3 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger1_offset|woodpecker_ac_lf_finger1 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger2_offset|woodpecker_ac_lf_finger2 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger4_offset|woodpecker_ac_lf_finger4 woodpecker_sk_lf_finger_1_1 woodpecker_sk_lf_finger_1_2 woodpecker_sk_lf_finger_1_3 woodpecker_sk_lf_finger_1_4 woodpecker_sk_lf_finger_2_1 woodpecker_sk_lf_finger_2_2 woodpecker_sk_lf_finger_2_3 woodpecker_sk_lf_finger_2_4 woodpecker_sk_lf_finger_4_1 woodpecker_sk_lf_finger_4_2 woodpecker_sk_lf_finger_4_3 woodpecker_sk_lf_finger_3_1 woodpecker_sk_lf_finger_3_2 woodpecker_sk_lf_finger_3_3 woodpecker_sk_rt_finger_3_1 woodpecker_sk_rt_finger_3_2 woodpecker_sk_rt_finger_3_3 woodpecker_sk_rt_finger_4_1 woodpecker_sk_rt_finger_4_2 woodpecker_sk_rt_finger_4_3 woodpecker_sk_rt_finger_2_2 woodpecker_sk_rt_finger_2_3 woodpecker_sk_rt_finger_2_4 woodpecker_sk_rt_finger_2_1 woodpecker_sk_rt_finger_1_1 woodpecker_sk_rt_finger_1_2 woodpecker_sk_rt_finger_1_3 woodpecker_sk_rt_finger_1_4 woodpecker_ac_lf_leg_settings woodpecker_ac_rt_leg_settings woodpecker_ac_lf_legPole woodpecker_ac_rt_legPole woodpecker_ac_lf_footIK woodpecker_ac_rt_footIK woodpecker_ac_rt_tail_settings woodpecker_ac_cn_tail_settings woodpecker_ac_lf_tail_settings woodpecker_ac_cn_tail_1 woodpecker_ac_cn_tail_2 woodpecker_ac_cn_pelvis woodpecker_ac_lf_clavicle woodpecker_ac_lf_shoulder woodpecker_ac_lf_elbow woodpecker_ac_rt_clavicle woodpecker_ac_rt_shoulder woodpecker_ac_rt_elbow woodpecker_ac_rt_wrink woodpecker_ac_lf_wrink woodpecker_ac_lf_wing_settings woodpecker_ac_rt_wing_settings woodpecker_ac_rt_kneeFK woodpecker_ac_rt_ankleFK woodpecker_ac_rt_fingerstFK woodpecker_ac_lf_kneeFK woodpecker_ac_lf_ankleFK woodpecker_ac_lf_fingerstFK woodpecker_ac_rt_hip woodpecker_ac_lf_hip woodpecker_ac_cn_free_chest woodpecker_ac_cn_base woodpecker_ac_cn_jaw\"" "abxPickerSelect \" woodpecker_ac_cn_upperbody woodpecker_ac_cn_spineFK1 woodpecker_ac_cn_spineFK2 woodpecker_ac_cn_spineFK2_inv woodpecker_ac_cn_spineFK1_inv woodpecker_ac_cn_chest woddpecker_ac_cn_neck_1 woddpecker_ac_cn_neck_2 woddpecker_ac_cn_head woodpecker_ac_cn_jaw woodpecker_ac_cn_tail_1 woodpecker_ac_cn_tail_2 woodpecker_ac_lf_clavicle woodpecker_ac_rt_clavicle woodpecker_ac_lf_hip woodpecker_ac_rt_hip woodpecker_ac_lf_shoulder woodpecker_ac_lf_elbow woodpecker_ac_lf_wrink woodpecker_ac_rt_shoulder woodpecker_ac_rt_elbow woodpecker_ac_rt_wrink woodpecker_ac_rt_wing_settings woodpecker_ac_lf_wing_settings woodpecker_ac_rt_footIK woodpecker_ac_lf_footIK woodpecker_ac_lf_legPole woodpecker_ac_rt_legPole woodpecker_ac_rt_kneeFK woodpecker_ac_rt_ankleFK woodpecker_ac_rt_fingerstFK woodpecker_ac_lf_kneeFK woodpecker_ac_lf_ankleFK woodpecker_ac_lf_fingerstFK woodpecker_sk_lf_finger_1_2 woodpecker_sk_lf_finger_1_3 woodpecker_sk_lf_finger_1_4 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger2_offset|woodpecker_ac_lf_finger2 woodpecker_sk_lf_finger_2_2 woodpecker_sk_lf_finger_2_3 woodpecker_sk_lf_finger_2_4 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger1_offset|woodpecker_ac_lf_finger1 woodpecker_sk_lf_finger_4_2 woodpecker_sk_lf_finger_4_3 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger4_offset|woodpecker_ac_lf_finger4 woodpecker_sk_lf_finger_3_2 woodpecker_sk_lf_finger_3_3 woodpecker_ac_rt_fingers_grp|woodpecker_ac_lf_finger3_offset|woodpecker_ac_lf_finger3 woodpecker_sk_rt_finger_2_2 woodpecker_sk_rt_finger_2_3 woodpecker_sk_rt_finger_2_4 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger1_offset|woodpecker_ac_lf_finger1 woodpecker_sk_rt_finger_1_2 woodpecker_sk_rt_finger_1_3 woodpecker_sk_rt_finger_1_4 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger2_offset|woodpecker_ac_lf_finger2 woodpecker_sk_rt_finger_4_2 woodpecker_sk_rt_finger_4_3 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger4_offset|woodpecker_ac_lf_finger4 woodpecker_sk_rt_finger_3_2 woodpecker_sk_rt_finger_3_3 woodpecker_ac_lf_fingers_grp|woodpecker_ac_lf_finger3_offset|woodpecker_ac_lf_finger3\"" "abxPickerSelect \" woodpecker_ac_cn_upperbody woodpecker_ac_cn_spineFK1 woodpecker_ac_cn_spineFK2 woodpecker_ac_cn_chest woodpecker_ac_rt_shoulder woodpecker_ac_rt_elbow woodpecker_ac_rt_wrink woodpecker_ac_lf_shoulder woodpecker_ac_lf_elbow woodpecker_ac_lf_wrink woddpecker_ac_cn_neck_1 woddpecker_ac_cn_head woodpecker_ac_lf_footIK woodpecker_ac_rt_footIK woodpecker_ac_rt_legPole woodpecker_ac_lf_legPole woodpecker_ac_rt_kneeFK woodpecker_ac_rt_ankleFK woodpecker_ac_rt_fingerstFK woodpecker_ac_lf_kneeFK woodpecker_ac_lf_ankleFK woodpecker_ac_lf_fingerstFK\""  ;
	setAttr ".image" -type "stringArray" 89 "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""  ;
	setAttr ".label" -type "stringArray" 89 "Root" "" "" "" "" "N1" "Head" "N2" "" "" "" "" "" "" "" "Sw" "Sw" "" "" "IK" "IK" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "IK" "IK" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "Fold" "Fold" "" "" "" "" "All" "Most" "Basic"  ;
	setAttr ".charPrefix" yes;
	setAttr ".pickerScale" 1;
select -ne :time1;
	setAttr ".o" 1;
	setAttr ".unw" 1;
select -ne :hardwareRenderingGlobals;
	setAttr ".vac" 2;
select -ne :renderPartition;
	setAttr -s 14 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 16 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderUtilityList1;
	setAttr -s 96 ".u";
select -ne :defaultRenderingList1;
select -ne :defaultTextureList1;
	setAttr -s 10 ".tx";
select -ne :initialShadingGroup;
	setAttr -s 72 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	setAttr ".ep" 1;
select -ne :defaultResolution;
	setAttr ".w" 640;
	setAttr ".h" 480;
	setAttr ".dar" 1.3333332538604736;
select -ne :defaultColorMgtGlobals;
	setAttr ".cme" no;
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
select -ne :ikSystem;
	setAttr -s 4 ".sol";
// End of woodpecker-pkr.ma
