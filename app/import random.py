import random

class Participant:
    def __init__(self, name, coins):
        self.name = name
        self.coins = coins

    def bet(self, bet_amount, choice):
        self.bet_amount = bet_amount
        self.choice = choice

def play_game(participants):
    results = []
    for participant in participants:
        if participant.coins >= participant.bet_amount:
            outcome = random.choices(
                ['win', 'draw', 'lose'],
                weights=[30, 20, 50],  # 승리 확률 30%, 무승부 20%, 패배 50%
                k=1
            )[0]
            if outcome == 'win':
                participant.coins += participant.bet_amount * 2  # 순이익은 배팅 금액의 2배
                result_text = f"{participant.name} - [{participant.bet_amount}코인] [{participant.choice} 선택] -> [{participant.coins}코인] (승리)"
            elif outcome == 'draw':
                result_text = f"{participant.name} - [{participant.bet_amount}코인] [{participant.choice} 선택] -> [{participant.coins}코인] (무승부)"
            else:  # 패배
                participant.coins -= participant.bet_amount
                result_text = f"{participant.name} - [{participant.bet_amount}코인] [{participant.choice} 선택] -> [{participant.coins}코인] (패배)"
            results.append(result_text)
        else:
            results.append(f"{participant.name}님은 배팅할 충분한 코인이 없습니다.")
    return results

def remove_bankrupt(participants):
    return [p for p in participants if p.coins > 0]

def main():
    participants = []
    print("가위바위보 배팅 게임에 오신 것을 환영합니다!")
    while True:
        action = input("참가자를 추가하려면 [A], 게임을 시작하려면 [P], 종료하려면 [Q]를 입력하세요: ").lower()
        if action == 'a':
            name = input("참가자의 이름을 입력하세요: ")
            coins = int(input("시작 코인을 입력하세요: "))
            participants.append(Participant(name, coins))
        elif action == 'p':
            if not participants:
                print("게임에 참여할 참가자가 없습니다.")
                continue
            for participant in participants:
                print(f"참가자: {participant.name}, 보유 코인: {participant.coins}")
                bet_amount = int(input(f"{participant.name}님, 배팅 금액을 입력하세요 (최소 100코인): "))
                while bet_amount < 100 or bet_amount > participant.coins:
                    bet_amount = int(input(f"잘못된 금액입니다. {participant.name}님, 배팅 금액을 다시 입력하세요 (최소 100코인): "))
                choice = input(f"{participant.name}님, 가위, 바위, 보 중 하나를 선택하세요: ")
                participant.bet(bet_amount, choice)
            results = play_game(participants)
            print("\n게임 결과:")
            for result in results:
                print(result)
            participants = remove_bankrupt(participants)
            if not participants:
                print("모든 참가자가 파산했습니다. 게임을 종료합니다.")
                break
        elif action == 'q':
            print("게임을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 'A', 'P', 'Q' 중 하나를 선택하세요.")

if __name__ == "__main__":
    main()