format 74

classinstance 128002 class_ref 128130 // GoClient
  name ""   xyz 28 4 2000 life_line_z 2000
classinstance 128130 class_ref 148610 // SymbolExtractorFactory
  name ""   xyz 106 4 2000 life_line_z 2000
classinstance 128898 class_ref 128386 // GoSymbolExtractor
  name ""   xyz 272 4 2000 life_line_z 2000
classinstance 129666 class_ref 128770 // SymbolSourceFactory
  name ""   xyz 413 4 2000 life_line_z 2000
classinstance 130434 class_ref 128642 // SymbolStorage
  name ""   xyz 564 4 2000 life_line_z 2000
durationcanvas 128258 classinstance_ref 128002 // :GoClient
  xyzwh 55 59 2010 11 49
  overlappingdurationcanvas 128642
    xyzwh 61 77 2020 11 25
  end
end
durationcanvas 128386 classinstance_ref 128130 // :SymbolExtractorFactory
  xyzwh 179 59 2010 11 29
end
durationcanvas 129026 classinstance_ref 128002 // :GoClient
  xyzwh 55 126 2010 11 52
  overlappingdurationcanvas 129410
    xyzwh 61 147 2020 11 25
  end
end
durationcanvas 129154 classinstance_ref 128898 // :GoSymbolExtractor
  xyzwh 331 126 2010 11 32
end
durationcanvas 129794 classinstance_ref 128002 // :GoClient
  xyzwh 55 197 2010 11 48
  overlappingdurationcanvas 130178
    xyzwh 61 214 2020 11 25
  end
end
durationcanvas 129922 classinstance_ref 129666 // :SymbolSourceFactory
  xyzwh 480 197 2010 11 28
end
durationcanvas 130946 classinstance_ref 128002 // :GoClient
  xyzwh 55 272 2010 11 40
end
durationcanvas 131074 classinstance_ref 130434 // :SymbolStorage
  xyzwh 611 272 2010 11 25
end
msg 128514 synchronous
  from durationcanvas_ref 128258
  to durationcanvas_ref 128386
  yz 59 2015 explicitmsg "getExtractor()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 82 42
msg 128770 synchronous
  from durationcanvas_ref 128386
  to durationcanvas_ref 128642
  yz 77 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
msg 129282 synchronous
  from durationcanvas_ref 129026
  to durationcanvas_ref 129154
  yz 126 2015 explicitmsg "extract()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 174 109
msg 129538 synchronous
  from durationcanvas_ref 129154
  to durationcanvas_ref 129410
  yz 147 2025 explicitmsg "getData()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 174 130
msg 130050 synchronous
  from durationcanvas_ref 129794
  to durationcanvas_ref 129922
  yz 197 2015 explicitmsg "getStorage()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 237 180
msg 130306 synchronous
  from durationcanvas_ref 129922
  to durationcanvas_ref 130178
  yz 214 2025 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
msg 131202 synchronous
  from durationcanvas_ref 130946
  to durationcanvas_ref 131074
  yz 272 2015 explicitmsg "store()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 319 255
end
