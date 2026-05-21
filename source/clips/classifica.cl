% --------------------------------------------------
% Classifica finale
% --------------------------------------------------

#include "partecipanti.cl".

% Partecipanti presenti
presente(P) :- partecipante(P).
presente(P) :- ongoing_partecipante(P,_).

% Vincoli sulla disponibilita del BYE
:- bye_assegnato(P,T1), bye_assegnato(P,T2), T1 < T2.

% Flag BYE
ha_bye(P,true) :- presente(P), bye_assegnato(P,_).
ha_bye(P,false) :- presente(P), not ha_bye(P,true).

% Punteggio e posizione
punti_totali(P,Tot) :-
	presente(P),
	Tot = #count { T : vittoria(P,T) }.

posizione(P,Pos) :-
	presente(P),
	punti_totali(P,Punti),
	Migliori = #count { Q : presente(Q), punti_totali(Q,AltriPunti), AltriPunti > Punti },
	Pos = 1 + Migliori.

% Uscita finale
classifica(P,Pos,Punti,Bye) :-
	presente(P),
	posizione(P,Pos),
	punti_totali(P,Punti),
	ha_bye(P,Bye).