#include "calendario.cl".

% Controlli di coerenza
test_fallito(classifica_incompleta) :- presente(P), not classifica(P,_,_,_).
test_fallito(incontro_senza_match) :- incontro(A,B,T), not match(A,B,_,T).
test_fallito(vincitore_non_coerente) :- match(A,B,V,_), V != A, V != B.
test_superato :- not test_fallito(_).

% Output mostrato dal python
#show turno/1.
#show partecipante/1.
#show ongoing_partecipante/2.
#show match/4.
#show bye_assegnato/2.
#show vittoria/2.

#show test_superato/0.
#show test_fallito/1.