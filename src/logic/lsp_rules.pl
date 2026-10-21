% Closed vocabulary; no user-supplied Prolog programs.
% class_count/1 must equal len(EXTENDED_ACTIONS) in config/actions.py (test_logic checks it).
class_count(68).
allowed_class(Class) :- integer(Class), class_count(Count), Class >= 0, Class < Count.
valid_prediction(Class, Confidence, Stable) :-
    allowed_class(Class), number(Confidence), integer(Stable),
    Confidence >= 0.85, Confidence =< 1.0, Stable >= 10.
emit_gloss(Class, Confidence, Stable) :-
    Class =\= 0, valid_prediction(Class, Confidence, Stable).
