from collections import defaultdict
from pathlib import Path
import json
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
# Prefer the renamed folder `source/clingo`; fall back to `source/clips` for compatibility
DEFAULT_PROGRAM_FILE = (BASE_DIR.parent / "source" / "clingo" / "test.cl").resolve()
if not DEFAULT_PROGRAM_FILE.exists():
    legacy = (BASE_DIR.parent / "source" / "clips" / "test.cl").resolve()
    if legacy.exists():
        DEFAULT_PROGRAM_FILE = legacy


def parse_atom(atom):
    atom = atom.strip()
    if "(" not in atom:
        return atom, []
    name, rest = atom.split("(", 1)
    args_str = rest[:-1]
    args = [arg.strip() for arg in args_str.split(",")] if args_str else []
    parsed = []
    for arg in args:
        if arg.isdigit():
            parsed.append(int(arg))
        else:
            parsed.append(arg)
    return name, parsed


def pick_best_witness(witnesses):
    if not witnesses:
        return None
    best = witnesses[0]
    best_cost = tuple(best.get("Costs", []))
    for witness in witnesses[1:]:
        cost = tuple(witness.get("Costs", []))
        if cost < best_cost:
            best = witness
            best_cost = cost
    return best


def run_clingo(program_file):
    cmd = [
        "clingo",
        program_file,
        "--outf=2",
        "--opt-mode=opt",
        "-n",
        "1",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode not in (10, 20, 30):
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    if not proc.stdout.strip():
        raise SystemExit("Nessun output da clingo.")
    return json.loads(proc.stdout)


def main():
    program_file = DEFAULT_PROGRAM_FILE
    if len(sys.argv) > 1:
        program_file = Path(sys.argv[1]).expanduser()
        if not program_file.is_absolute():
            program_file = (Path.cwd() / program_file).resolve()
    data = run_clingo(str(program_file))
    calls = data.get("Call", [])
    witnesses = []
    if calls:
        witnesses = calls[0].get("Witnesses", [])

    best = pick_best_witness(witnesses)
    if best is None:
        print("Nessun modello trovato.")
        return

    atoms = best.get("Value", [])

    matches_by_turn = defaultdict(list)
    bye_by_turn = defaultdict(list)
    victories_by_player = defaultdict(set)
    player_entry_turn = {}
    turns = set()
    test_failed = []
    test_ok = False

    for atom in atoms:
        name, args = parse_atom(atom)
        if name == "match" and len(args) == 4:
            a, b, winner, turn = args
            matches_by_turn[int(turn)].append((str(a), str(b), str(winner)))
        elif name == "bye_assegnato" and len(args) == 2:
            player, turn = args
            bye_by_turn[int(turn)].append(str(player))
        elif name == "vittoria" and len(args) == 2:
            player, turn = args
            victories_by_player[str(player)].add(int(turn))
        elif name == "turno" and len(args) == 1:
            turns.add(int(args[0]))
        elif name == "partecipante" and len(args) == 1:
            player = str(args[0])
            player_entry_turn[player] = min(player_entry_turn.get(player, 1), 1)
        elif name == "ongoing_partecipante" and len(args) == 2:
            player = str(args[0])
            entry_turn = int(args[1])
            if player in player_entry_turn:
                player_entry_turn[player] = min(player_entry_turn[player], entry_turn)
            else:
                player_entry_turn[player] = entry_turn
        elif name == "test_fallito" and len(args) == 1:
            test_failed.append(str(args[0]))
        elif name == "test_superato":
            test_ok = True

    summary_turns = set(turns) | set(matches_by_turn.keys()) | set(bye_by_turn.keys())

    for turn, matches in matches_by_turn.items():
        for a, b, _winner in matches:
            player_entry_turn[a] = min(player_entry_turn.get(a, turn), turn)
            player_entry_turn[b] = min(player_entry_turn.get(b, turn), turn)
    for turn, players in bye_by_turn.items():
        for player in players:
            player_entry_turn[player] = min(player_entry_turn.get(player, turn), turn)

    def present_players(turn):
        return {player for player, entry_turn in player_entry_turn.items() if turn >= entry_turn}

    def points_until_turn(player, turn):
        wins = victories_by_player.get(player, set())
        return sum(1 for w_turn in wins if w_turn <= turn)

    def has_bye_until_turn(player, turn):
        for bye_turn in bye_by_turn:
            if bye_turn <= turn and player in bye_by_turn[bye_turn]:
                return True
        return False

    for turn in sorted(summary_turns):
        print(f"--- Turno {turn} ---")

        matches = sorted(matches_by_turn.get(turn, []), key=lambda m: (m[0], m[1]))
        if matches:
            for a, b, winner in matches:
                print(f"{a} vs {b} con {winner} vincitore")
        else:
            print("Nessun incontro")

        byes = sorted(bye_by_turn.get(turn, []))
        if byes:
            print(f"BYE assegnato a {', '.join(byes)}")
        else:
            print("BYE assegnato a nessuno")

        print(f"Classifica al turno {turn}:")
        players = sorted(present_players(turn))
        player_points = {player: points_until_turn(player, turn) for player in players}
        standings = []
        for player in players:
            points = player_points[player]
            better = sum(1 for other in players if player_points[other] > points)
            pos = 1 + better
            bye = "true" if has_bye_until_turn(player, turn) else "false"
            standings.append((pos, player, points, bye))
        standings.sort(key=lambda s: (s[0], s[1]))
        for pos, player, points, bye in standings:
            bye_label = "si" if bye == "true" else "no"
            punti_label = "punto" if points == 1 else "punti"
            print(f"{pos}) {player} - {points} {punti_label} - BYE: {bye_label}")
        print()

    if test_ok and not test_failed:
        print("Esito test: SUPERATO")
    else:
        print("Esito test: FALLITO")
        for failure in sorted(test_failed):
            print(f"- {failure}")


if __name__ == "__main__":
    main()