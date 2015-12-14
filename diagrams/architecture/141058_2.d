format 74

classinstance 128002 class_ref 128130 // GoClient
  name ""   xyz 41 4 2000 life_line_z 2000
classinstance 129410 class_ref 128386 // GoSymbolExtractor
  name ""   xyz 307 4 2000 life_line_z 2000
classinstance 130178 class_ref 128770 // SymbolSourceFactory
  name ""   xyz 444 4 2000 life_line_z 2000
classinstance 130946 class_ref 128642 // SymbolStorage
  name ""   xyz 594 4 2000 life_line_z 2000
classinstance 131714 class_ref 135554 // GoApiComparator
  name ""   xyz 702 4 2000 life_line_z 2000
classinstance 133250 class_ref 148610 // SymbolExtractorFactory
  name ""   xyz 139 4 2000 life_line_z 2000
durationcanvas 129538 classinstance_ref 128002 // :GoClient
  xyzwh 68 136 2010 11 51
  overlappingdurationcanvas 129922
    xyzwh 74 156 2020 11 25
  end
end
durationcanvas 129666 classinstance_ref 129410 // :GoSymbolExtractor
  xyzwh 366 136 2010 11 31
end
durationcanvas 130306 classinstance_ref 128002 // :GoClient
  xyzwh 68 214 2010 11 50
  overlappingdurationcanvas 130690
    xyzwh 74 233 2020 11 25
  end
end
durationcanvas 130434 classinstance_ref 130178 // :SymbolSourceFactory
  xyzwh 511 214 2010 11 30
end
durationcanvas 131074 classinstance_ref 128002 // :GoClient
  xyzwh 68 299 2010 11 48
  overlappingdurationcanvas 131458
    xyzwh 74 316 2020 11 25
  end
end
durationcanvas 131202 classinstance_ref 130946 // :SymbolStorage
  xyzwh 641 299 2010 11 28
end
durationcanvas 131842 classinstance_ref 128002 // :GoClient
  xyzwh 68 374 2010 11 50
  overlappingdurationcanvas 132226
    xyzwh 74 393 2020 11 25
  end
end
durationcanvas 131970 classinstance_ref 131714 // :GoApiComparator
  xyzwh 756 374 2010 11 30
end
durationcanvas 133378 classinstance_ref 128002 // :GoClient
  xyzwh 68 65 2010 11 52
  overlappingdurationcanvas 133762
    xyzwh 74 86 2020 11 25
  end
end
durationcanvas 133506 classinstance_ref 133250 // :SymbolExtractorFactory
  xyzwh 212 65 2010 11 32
end
msg 129794 synchronous
  from durationcanvas_ref 129538
  to durationcanvas_ref 129666
  yz 136 2015 explicitmsg "extract()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 192 119
msg 130050 synchronous
  from durationcanvas_ref 129666
  to durationcanvas_ref 129922
  yz 156 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
msg 130562 synchronous
  from durationcanvas_ref 130306
  to durationcanvas_ref 130434
  yz 214 2015 explicitmsg "getStorage()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 252 197
msg 130818 synchronous
  from durationcanvas_ref 130434
  to durationcanvas_ref 130690
  yz 233 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
msg 131330 synchronous
  from durationcanvas_ref 131074
  to durationcanvas_ref 131202
  yz 299 2015 explicitmsg "getData()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 314 282
msg 131586 synchronous
  from durationcanvas_ref 131202
  to durationcanvas_ref 131458
  yz 316 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
msg 132098 synchronous
  from durationcanvas_ref 131842
  to durationcanvas_ref 131970
  yz 374 2015 explicitmsg "compareAPI()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 421 357
msg 132354 synchronous
  from durationcanvas_ref 131970
  to durationcanvas_ref 132226
  yz 393 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
msg 133634 synchronous
  from durationcanvas_ref 133378
  to durationcanvas_ref 133506
  yz 65 2015 explicitmsg "getExtractor()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 110 48
msg 133890 synchronous
  from durationcanvas_ref 133506
  to durationcanvas_ref 133762
  yz 86 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
end
