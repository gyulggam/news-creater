"""
스케줄러 테스트용 파일
실시간 알림 기능을 테스트하기 위해 1분 후에 알림을 보내는 설정
"""

from datetime import datetime, time, timedelta

def get_test_notification_times():
    """테스트용 알림 시간 - 현재시간에서 1분, 2분, 3분 후"""
    now = datetime.now()
    
    test_times = []
    for minutes_later in [1, 2, 3]:
        future_time = now + timedelta(minutes=minutes_later)
        test_times.append(time(future_time.hour, future_time.minute))
    
    return test_times

if __name__ == "__main__":
    test_times = get_test_notification_times()
    print("🕐 테스트 알림 시간:")
    for i, t in enumerate(test_times, 1):
        print(f"  {i}. {t.strftime('%H:%M')}") 