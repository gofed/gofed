format 74

classinstance 128130 class_ref 128130 // GoClient
  name ""   xyz 71 4 2000 life_line_z 2000
classinstance 128258 class_ref 128386 // GoSymbolExtractor
  name ""   xyz 325 4 2000 life_line_z 2000
classinstance 129154 class_ref 135298 // GoSymbolsTransformator
  name ""   xyz 465 4 2000 life_line_z 2000
classinstance 131330 class_ref 128514 // Specker.JsonParser
  name ""   xyz 635 4 2000 life_line_z 2000
classinstance 134530 class_ref 128386 // GoSymbolExtractor
  name ""   xyz 168 4 2000 life_line_z 2000
durationcanvas 128386 classinstance_ref 128130 // :GoClient
  xyzwh 98 126 2010 11 52
  overlappingdurationcanvas 131074
    xyzwh 104 147 2020 11 25
  end
end
durationcanvas 128514 classinstance_ref 128258 // :GoSymbolExtractor
  xyzwh 384 126 2010 11 32
end
durationcanvas 130178 classinstance_ref 128130 // :GoClient
  xyzwh 98 190 2010 11 67
  overlappingdurationcanvas 130818
    xyzwh 104 214 2020 11 31
  end
end
durationcanvas 130306 classinstance_ref 129154 // :GoSymbolsTransformator
  xyzwh 542 189 2010 11 69
end
durationcanvas 131458 classinstance_ref 128130 // :GoClient
  xyzwh 98 291 2010 11 40
end
durationcanvas 131586 classinstance_ref 131330 // :Specker.JsonParser
  xyzwh 696 293 2010 11 42
end
durationcanvas 132994 classinstance_ref 131330 // :Specker.JsonParser
  xyzwh 696 422 2010 11 32
end
durationcanvas 133122 classinstance_ref 128130 // :GoClient
  xyzwh 98 422 2010 11 32
end
durationcanvas 134146 classinstance_ref 128130 // :GoClient
  xyzwh 98 362 2010 11 41
end
durationcanvas 134274 classinstance_ref 131330 // :Specker.JsonParser
  xyzwh 696 362 2010 11 26
end
durationcanvas 135298 classinstance_ref 128130 // :GoClient
  xyzwh 98 63 2010 11 52
  overlappingdurationcanvas 135682
    xyzwh 104 84 2020 11 25
  end
end
durationcanvas 135426 classinstance_ref 134530 // :GoSymbolExtractor
  xyzwh 227 63 2010 11 32
end
msg 128642 synchronous
  from durationcanvas_ref 128386
  to durationcanvas_ref 128514
  yz 126 2015 explicitmsg "extract()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 132 109
msg 130434 synchronous
  from durationcanvas_ref 130178
  to durationcanvas_ref 130306
  yz 204 2015 explicitmsg "transformToSpecData()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 222 187
msg 130946 synchronous
  from durationcanvas_ref 130306
  to durationcanvas_ref 130818
  yz 228 2025 explicitmsg "getData()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 266 211
msg 131202 synchronous
  from durationcanvas_ref 128514
  to durationcanvas_ref 131074
  yz 147 3005 explicitmsg "getData()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 168 130
msg 131714 synchronous
  from durationcanvas_ref 131458
  to durationcanvas_ref 131586
  yz 293 2015 explicitmsg "parse()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 362 276
msg 133250 synchronous
  from durationcanvas_ref 132994
  to durationcanvas_ref 133122
  yz 422 2015 explicitmsg "getSpecfile()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 341 405
msg 134402 synchronous
  from durationcanvas_ref 134146
  to durationcanvas_ref 134274
  yz 362 2015 explicitmsg "applyChange()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 336 345
msg 135554 synchronous
  from durationcanvas_ref 135298
  to durationcanvas_ref 135426
  yz 63 2015 explicitmsg "getExtractor()"
  show_full_operations_definition default drawing_language default show_context_mode default
  label_xy 128 46
msg 135810 synchronous
  from durationcanvas_ref 135426
  to durationcanvas_ref 135682
  yz 84 3005 unspecifiedmsg
  show_full_operations_definition default drawing_language default show_context_mode default
end
