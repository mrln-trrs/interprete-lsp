% Closed vocabulary; no user-supplied Prolog programs.
allowed_class(0). allowed_class(1). allowed_class(2).
allowed_class(3). allowed_class(4). allowed_class(5).
allowed_class(6). allowed_class(7). allowed_class(8).
valid_prediction(Class, Confidence, Stable) :-
    allowed_class(Class), number(Confidence), integer(Stable),
    Confidence >= 0.85, Confidence =< 1.0, Stable >= 10.
emit_gloss(Class, Confidence, Stable) :-
    Class =\= 0, valid_prediction(Class, Confidence, Stable).
