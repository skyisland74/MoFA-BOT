import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
import os 

# 봇 설정
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ 알림을 보낼 채널 ID 설정 (원하는 채널 ID로 변경)
ALERT_CHANNEL_ID = 1322900647619723334  # 🚨 알림을 받을 채널의 ID 입력!

# 예약 저장소
reservations = {}

def convert_meridiem(meridiem):
    """오전/오후 → AM/PM 변환"""
    return "AM" if meridiem == "오전" else "PM"

@bot.tree.command(name="투어예약", description="투어를 예약합니다.")
@app_commands.describe(
    날짜="예약 날짜 (YYYY-MM-DD)",
    시간="시간 (hh:mm)",
    오전오후="오전 또는 오후",
    방문국가="방문할 국가"
)
async def tour_reserve(interaction: discord.Interaction, 날짜: str, 시간: str, 오전오후: str, 방문국가: str):
    """투어 예약 명령어"""
    am_pm = convert_meridiem(오전오후)
    full_time = f"{날짜} {시간} {am_pm}"

    try:
        parsed_time = datetime.strptime(full_time, "%Y-%m-%d %I:%M %p")
    except ValueError:
        await interaction.response.send_message("좀 맞춰써봐 (예: 2025-04-03 06:35 오후)", ephemeral=True)
        return

    # 예약 저장
    reservations[full_time] = {
        "user": interaction.user.name,
        "국가": 방문국가,
        "channel": interaction.channel.id,
    }

    # ✅ 예약 완료 메시지
    embed = discord.Embed(title="예약 완료", color=0x00FF00)
    embed.add_field(name="날짜", value=날짜)
    embed.add_field(name="시간", value=f"{시간} {오전오후}")
    embed.add_field(name="방문 국가", value=방문국가)
    embed.set_footer(text=f"예약자: {interaction.user.name}")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="투어삭제", description="예약된 투어를 삭제합니다.")
async def tour_delete(interaction: discord.Interaction):
    """예약 삭제 명령어"""
    if not reservations:
        await interaction.response.send_message("투어 예약된거 없는뎅", ephemeral=True)
        return

    # 예약 목록 출력
    embed = discord.Embed(title="🗑 예약 목록", color=0xFFA500)
    reservation_list = list(reservations.keys())

    for idx, (time, info) in enumerate(reservations.items(), start=1):
        embed.add_field(name=f"{idx}. {time}", value=f"{info['국가']} - {info['user']}", inline=False)

    await interaction.response.send_message(embed=embed)

    # 숫자 입력 대기
    def check(msg):
        return msg.author == interaction.user and msg.content.isdigit()

    try:
        msg = await bot.wait_for("message", check=check, timeout=30.0)
        idx = int(msg.content) - 1

        if 0 <= idx < len(reservation_list):
            deleted_time = reservation_list[idx]
            del reservations[deleted_time]
            await interaction.channel.send(f"🗑 `{deleted_time}` 투어 예약이 삭제되었습니다")
        else:
            await interaction.channel.send("다시해 빠가야")

    except TimeoutError:
        await interaction.channel.send("시간 초과")

NN = 1321051972857499742  # 🔹 멘션할 역할 ID를 여기에 입력

@tasks.loop(minutes=1)
async def check_tour():
    """예약된 시간에 맞춰 알림 전송"""
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    if now in reservations:
        tour = reservations.pop(now)

        # ✅ 알림 채널 가져오기
        channel = bot.get_channel(ALERT_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="🚨 투어 알림", color=0xFF0000)
            embed.add_field(name="📅 날짜", value=now.split()[0])
            embed.add_field(name="⏰ 시간", value=now.split()[1] + " " + now.split()[2])
            embed.add_field(name="🌍 방문 국가", value=tour["국가"])
            embed.add_field(name="👤 예약자", value=tour["user"])
            
            # ✅ 특정 역할 멘션 추가
            role_mention = f"<@&{NN}>"  # 🔹 역할 ID를 멘션 형식으로 변환
            await channel.send(f"{role_mention}", embed=embed)
        else:
            print("🚨 알림 채널을 찾을 수 없습니다.")


@bot.event
async def on_ready():
    print(f"✅ {bot.user} 로그인 완료!")
    check_tour.start()  # 자동 알림 시작

access_token = os.environ['BOT_TOKEN']
bot.run("access_token")  # 🚨 여기에 봇 토큰 입력!
