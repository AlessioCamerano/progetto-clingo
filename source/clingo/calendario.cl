#include "partecipanti.cl".
#include "classifica.cl".

% Turni
turno(1..6).

% Partecipanti attivi
attivo(P,T) :- partecipante(P), turno(T).
attivo(P,T) :- ongoing_partecipante(P,TIngresso), turno(T), T >= TIngresso.

% Coppie candidate
coppia(A,B,T) :- attivo(A,T), attivo(B,T), A < B.

% Incontri scelti
{ incontro(A,B,T) : coppia(A,B,T) }.

% Un partecipante non puo' essere coinvolto in piu' di un incontro nello stesso turno
coinvolge(P,A,B,T) :- incontro(A,B,T), A = P.
coinvolge(P,A,B,T) :- incontro(A,B,T), B = P.
:- attivo(P,T), 2 <= #count { A,B : coinvolge(P,A,B,T) }.

partecipante_in_incontro(P,T) :- coinvolge(P,_,_,T).

% Gestione BYE
:- attivo(P,T), not bye_assegnato(P,T), not partecipante_in_incontro(P,T).
:- attivo(P,T), bye_assegnato(P,T), partecipante_in_incontro(P,T).

{ bye_assegnato(P,T) } :- attivo(P,T).

num_attivi(T,N) :- turno(T), N = #count { P : attivo(P,T) }.
num_bye(T,B) :- turno(T), B = #count { P : bye_assegnato(P,T) }.

% Se gli attivi sono dispari serve un solo BYE, altrimenti nessuno
:- num_attivi(T,N), num_bye(T,B), B != N \ 2.

% Il BYE puo' essere assegnato una sola volta a ciascun partecipante
:- bye_assegnato(P,T1), bye_assegnato(P,T2), T1 < T2.

vittoria(P,T) :- bye_assegnato(P,T).

% Un solo incontro per coppia
:- incontro(A,B,T1), incontro(A,B,T2), T1 < T2.

1 { vittoria(A,T); vittoria(B,T) } 1 :- incontro(A,B,T).

% Output del match
match(A,B,A,T) :- incontro(A,B,T), vittoria(A,T).
match(A,B,B,T) :- incontro(A,B,T), vittoria(B,T).

% Punteggio prima del turno per favorire gli spareggi
punti_prima_turno(P,T,S) :-
	attivo(P,T),
	S = #count { TR : vittoria(P,TR), TR < T }.

% Differenza punti nel pairing
diff_punti(A,B,T,D) :-
	incontro(A,B,T),
	punti_prima_turno(A,T,SA),
	punti_prima_turno(B,T,SB),
	D = |SA - SB|.

% Obiettivo finale
#minimize { D@1,A,B,T : diff_punti(A,B,T,D) }.