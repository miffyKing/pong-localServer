# chatApp/consumers.py
import json
import asyncio
# from aredis import StrictRedis
# from channels.layers import get_channel_layer


from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):

    # play_bar1_position = 0
    # play_bar2_position = 0
    play_bar1_position = {'x':0, 'y':9}
    play_bar2_position = {'x':0, 'y':-9}

    ball_position = {'x':0, 'y' : 0}
    ball_velocity = {'x': 0.15, 'y': 0.1}  # 공의 속도

    score_player1 = 0;
    score_player2 = 0;

    # game_board_size_x = 10
    # game_board_size_y = 10

    # rectangle = [(-5, 5), (5, 5), (-5, -5), (5, -5)]

    async def connect(self):
        # self.redis = StrictRedis(host='localhost', port=6379, db=0)
        await self.accept()
        asyncio.create_task(self.ball_position_updater())

    async def disconnect(self, close_code):
        # self.redis.close()
        # await self.redis.wait_closed()
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # 클라이언트로부터 'w' 또는 's' 입력 받기
        # 첫 번째 플레이어의 바 이동
        if message == 'a':
            # 왼쪽으로 이동할 때는 'x' 좌표를 감소시킵니다.
            self.play_bar1_position['x'] = max(-9, self.play_bar1_position['x'] - 0.4)
        elif message == 'd':
            # 오른쪽으로 이동할 때는 'x' 좌표를 증가시킵니다.
            self.play_bar1_position['x'] = min(9, self.play_bar1_position['x'] + 0.4)

        # 두 번째 플레이어의 바 이동
        if message == 'j':
            # 왼쪽으로 이동할 때는 'x' 좌표를 감소시킵니다.
            self.play_bar2_position['x'] = max(-9, self.play_bar2_position['x'] - 0.4)
        elif message == 'l':
            # 오른쪽으로 이동할 때는 'x' 좌표를 증가시킵니다.
            self.play_bar2_position['x'] = min(9, self.play_bar2_position['x'] + 0.4)

        self._update_ball_position()
        # 변경된 바 위치를 모든 클라이언트에 전송
        

    async def _update_ball_position(self):
        # 공 위치 업데이트
        self.ball_position['x'] += self.ball_velocity['x']
        self.ball_position['y'] += self.ball_velocity['y']
        
        # 바와 공의 충돌 검사
        # 바의 가로 길이 및 공의 크기를 고려해야 함
        bar_width = 2  # 예시 값, 실제 바의 가로 길이에 맞게 조정
        ball_radius = 0.5  # 예시 값, 실제 공의 반지름에 맞게 조정
        
        # # 첫 번째 플레이어 바와 공의 충돌 검사
        if self.play_bar1_position['y'] - ball_radius < self.ball_position['y'] < self.play_bar1_position['y'] + ball_radius \
        and self.play_bar1_position['x'] - bar_width / 2 < self.ball_position['x'] < self.play_bar1_position['x'] + bar_width / 2:
            self.ball_velocity['y'] *= -1  # y 방향 반전
            
        # # 두 번째 플레이어 바와 공의 충돌 검사
        if self.play_bar2_position['y'] - ball_radius < self.ball_position['y'] < self.play_bar2_position['y'] + ball_radius \
        and self.play_bar2_position['x'] - bar_width / 2 < self.ball_position['x'] < self.play_bar2_position['x'] + bar_width / 2:
            self.ball_velocity['y'] *= -1  # y 방향 반전
        
        # 벽과의 충돌 처리
        if self.ball_position['y'] <= -10 or self.ball_position['y'] >= 10: ## up ,down wall collision
            if self.ball_position['y'] > 10:         # collision on upper side wall, player2 score up
                self.score_player2 += 1
                print("!!!!!!!!!!!!!!!!")
                await self._reset_ball_and_pause()
            elif self.ball_position['y'] < -10:       ## collision on bottom side wall,player1 score up 
                self.score_player1 += 1
                print("????????????")
                await self._reset_ball_and_pause()
            # self.ball_velocity['y'] *= -1  # x 방향 반전
        if self.ball_position['x'] <= -10 or self.ball_position['x'] >= 10: ## left, right wall collision
            self.ball_velocity['x'] *= -1  # x 방향 반전
        

        # 모든 클라이언트에 변경된 정보 전송
        await self.send(text_data=json.dumps({
            'play_bar1_position': self.play_bar1_position,
            'play_bar2_position': self.play_bar2_position,
            'ball_position': self.ball_position,
            'score_player1': self.score_player1,
            'score_player2': self.score_player2
        }))
        # await self.send( )



    async def _reset_ball_and_pause(self):
        # 공의 위치를 중앙으로 초기화
        self.ball_position = {'x': 0, 'y': 0}
        self.play_bar1_position = {'x':0, 'y':9}
        self.play_bar2_position = {'x':0, 'y': -9}
        
        # 공의 속도를 초기화하거나, 원하는 초기 속도로 설정할 수 있습니다.
        import random
        self.ball_velocity = {'x': random.choice([0.15, -0.15]), 'y': random.choice([0.15, -0.15])}
   
        # 점수 업데이트 후 1초간 휴식
        await asyncio.sleep(1)

    async def ball_position_updater(self):
        while True:
            await self._update_ball_position()
            await asyncio.sleep(0.02)  # 1초마다 공 위치 업데이트
            # print(self.ball_position + " " + self.play_bar1_position + " " + self.play_bar2_position);
            dx = self.ball_velocity['x']
            dy = self.ball_velocity['y']
            if dx != 0:
                slope = dy / dx
                print(f"Ball Position: {self.ball_position}, Bar1 Position: {self.play_bar1_position}, Bar2 Position: {self.play_bar2_position}, Slope: {slope}")
            else:
                print(f"Ball Position: {self.ball_position}, Bar1 Position: {self.play_bar1_position}, Bar2 Position: {self.play_bar2_position}, Slope: vertical")
