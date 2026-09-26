import os
import asyncio
import datetime
import pytz
from flask import Flask, render_template_string, request, jsonify
from threading import Thread
import discord
from discord.ext import commands

# ==========================================
# ⚙️ CONFIGURATION (การตั้งค่า)
# ==========================================
TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"  # ใส่ Token ของ Bot

GUILD_ID = 1549058616936366202        # Server ID
VERIFY_ROLE_ID = 1549371491731120139  # Role ID ที่จะแจกเมื่อยืนยันสำเร็จ
LOG_CHANNEL_ID = 1553435066158284920  # Channel ID สำหรับส่ง Log

# ลิงก์ OAuth2 ของคุณ
OAUTH2_URL = "https://discord.com/oauth2/authorize?client_id=1553436773684744262&response_type=code&redirect_uri=https%3A%2F%2Fdiscord-vertify.onrender.com%2Fcallback&scope=identify"

# ลิงก์รูป GIF ของคุณ
GIF_URL = "https://cdn.discordapp.com/attachments/1531546035996856410/1531620024312266842/Tumblr_l_694101025772370-1-1-1-2-1-1-1-1-2.gif?ex=6ab8f9cd&is=6ab7a84d&hm=fac12674ffc2a8abaacaec0e461c9c28ab6979524fd16a4ad426b6e9bbfe7bbf&"

# ==========================================
# 🌐 FLASK WEB SERVER SETUP
# ==========================================
app = Flask(__name__, static_folder=".", static_url_path="")

@app.route('/')
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return render_template_string(html_content)
    except Exception as e:
        return f"Error loading index.html: {e}", 500

@app.route('/api/give-role', methods=['POST'])
def give_role_api():
    data = request.json or {}
    user_id = data.get('user_id')

    print("------------------------------------------")
    print(f"📥 Received API Request for User ID: {user_id}")
    print("------------------------------------------")

    if not user_id:
        print("❌ Error: Missing user_id in request payload")
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    try:
        user_id_int = int(user_id)
        future = asyncio.run_coroutine_threadsafe(
            process_verification(user_id_int),
            bot.loop
        )
        result = future.result(timeout=10)
        return jsonify(result)
    except Exception as e:
        print(f"❌ Exception in /api/give-role: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# 🤖 DISCORD BOT SETUP
# ==========================================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("==========================================")
    print(f"🤖 Bot Logged in as: {bot.user.name} ({bot.user.id})")
    print(f"🌐 Web Server Running on Port 8080")
    print("==========================================")

async def process_verification(user_id: int):
    print("------------------------------------------")
    print(f"🔄 Processing verification for ID: {user_id}...")
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Error: Guild not found! Check GUILD_ID.")
        print("------------------------------------------")
        return {"status": "error", "message": "Guild not found"}

    member = guild.get_member(user_id)
    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except Exception as e:
            print(f"❌ Error fetching member {user_id}: {e}")
            print("------------------------------------------")
            return {"status": "error", "message": "Member not found in server"}

    role = guild.get_role(VERIFY_ROLE_ID)
    if not role:
        print("❌ Error: Role not found! Check VERIFY_ROLE_ID.")
        print("------------------------------------------")
        return {"status": "error", "message": "Role not found"}

    # 1. แจกยศ
    try:
        await member.add_roles(role)
        print(f"✅ Successfully added role to {member.name}")
    except discord.Forbidden:
        print("❌ Forbidden: Bot role is LOWER than the target role in Server Settings!")
        print("------------------------------------------")
        return {"status": "error", "message": "Bot doesn't have permission to add this role."}

    # 2. ส่ง Log ลงห้อง Log Channel พร้อมภาพ GIF
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        tz = pytz.timezone('Asia/Bangkok')
        current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        embed = discord.Embed(
            title="✅ ยืนยันตัวตนสำเร็จ",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **ผู้ใช้งาน:** <@{member.id}>\n"
                f"⏰ **เวลา:** `{current_time}`\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x2ecc71
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=GIF_URL)  # 👈 แสดงภาพ GIF คั่นท้าย Embed
        await log_channel.send(embed=embed)
        print(f"📢 Log sent to channel {LOG_CHANNEL_ID}")
    else:
        print("❌ Error: Log channel not found! Check LOG_CHANNEL_ID.")

    print("------------------------------------------")
    return {"status": "success", "message": f"Successfully verified {member.name}"}

# ==========================================
# 💬 COMMANDS SETUP
# ==========================================
@bot.command(aliases=['setup_vertify'])
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(
        title="IDONTKNOW ON TOP",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "ุยืนยันตนผ่าน Web สามารถกดด้านล่างเพื่อทำการยืนยันตัวตน\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x5865F2
    )
    embed.set_image(url=GIF_URL)  # 👈 แสดงภาพ GIF คั่นท้าย Embed
    
    button = discord.ui.Button(
        label="Verify Here",
        url=f"{OAUTH2_URL}&state={ctx.author.id}",
        style=discord.ButtonStyle.link
    )
    
    view = discord.ui.View()
    view.add_item(button)
    
    await ctx.send(embed=embed, view=view)

# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    bot.run(TOKEN)
