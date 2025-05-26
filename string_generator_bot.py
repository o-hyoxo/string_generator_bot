import os
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取配置
API_ID = int(os.getenv("API_ID", "24369670"))
API_HASH = os.getenv("API_HASH", "1d9a1f3aefe6e65bcfa51a35ba103735")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# 创建机器人客户端 - 机器人也需要API_ID和API_HASH
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 存储用户会话状态
user_sessions = {}

@bot.on_message(filters.command("start"))
async def start(_, message):
    welcome_text = """
🤖 **Pyrogram字符串生成器**

欢迎使用！我可以帮你生成Pyrogram会话字符串。

📱 使用方法：
• 发送 /gen 开始生成
• 按照提示输入手机号码
• 输入验证码
• 如果启用了两步验证，请输入密码

⚠️ **重要提醒：**
• 请确保你的API ID和API Hash正确
• 手机号码请使用国际格式（如：+8613812345678）
• 生成的字符串请妥善保管，不要泄露给他人

开始使用请发送 /gen
    """
    await message.reply(welcome_text, parse_mode="markdown")

@bot.on_message(filters.command("gen"))
async def generate_string(_, message):
    user_id = message.from_user.id
    
    # 清理旧的会话状态
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await message.reply("📱 请发送你的手机号码（国际格式，例如：+8613812345678）:")
    
    # 设置用户状态
    user_sessions[user_id] = {"step": "waiting_phone"}

@bot.on_message(filters.text & filters.private)
async def handle_text(_, message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        return
    
    session_data = user_sessions[user_id]
    step = session_data.get("step")
    
    if step == "waiting_phone":
        phone = message.text.strip()
        
        # 基本的手机号码验证
        if not phone.startswith("+") or len(phone) < 10:
            await message.reply("❌ 手机号码格式不正确！请使用国际格式，例如：+8613812345678")
            return
        
        try:
            # 创建临时客户端发送验证码
            temp_client = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
            await temp_client.connect()
            
            sent_code = await temp_client.send_code(phone)
            await temp_client.disconnect()
            
            session_data.update({
                "step": "waiting_code",
                "phone": phone,
                "phone_code_hash": sent_code.phone_code_hash
            })
            
            await message.reply("✅ 验证码已发送！请输入你收到的验证码:")
            
        except Exception as e:
            logger.error(f"发送验证码时出错: {e}")
            await message.reply(f"❌ 发送验证码失败: {str(e)}")
            if user_id in user_sessions:
                del user_sessions[user_id]
    
    elif step == "waiting_code":
        code = message.text.strip()
        phone = session_data["phone"]
        phone_code_hash = session_data["phone_code_hash"]
        
        try:
            # 创建新的客户端进行登录
            user_client = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
            await user_client.connect()
            
            try:
                await user_client.sign_in(phone, phone_code_hash, code)
                
                # 登录成功，导出会话字符串
                session_string = await user_client.export_session_string()
                await user_client.disconnect()
                
                await message.reply(
                    f"🎉 **会话字符串生成成功！**\n\n"
                    f"`{session_string}`\n\n"
                    f"⚠️ **请妥善保管此字符串，不要泄露给他人！**",
                    parse_mode="markdown"
                )
                
                # 清理会话状态
                if user_id in user_sessions:
                    del user_sessions[user_id]
                    
            except SessionPasswordNeeded:
                await user_client.disconnect()
                session_data["step"] = "waiting_password"
                session_data["temp_client_session"] = user_client.session_string
                await message.reply("🔒 检测到两步验证！请输入你的两步验证密码:")
                
        except Exception as e:
            logger.error(f"登录时出错: {e}")
            await message.reply(f"❌ 登录失败: {str(e)}")
            if user_id in user_sessions:
                del user_sessions[user_id]
    
    elif step == "waiting_password":
        password = message.text.strip()
        
        try:
            # 使用保存的会话继续登录
            user_client = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
            await user_client.connect()
            
            # 重新进行登录流程
            phone = session_data["phone"]
            sent_code = await user_client.send_code(phone)
            
            # 这里需要用户重新输入验证码，但为了简化流程，我们提示用户重新开始
            await user_client.disconnect()
            await message.reply(
                "❌ 两步验证处理复杂，请重新发送 /gen 开始，"
                "并确保你记得两步验证密码。"
            )
            
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except Exception as e:
            logger.error(f"两步验证时出错: {e}")
            await message.reply(f"❌ 两步验证失败: {str(e)}")
            if user_id in user_sessions:
                del user_sessions[user_id]

@bot.on_message(filters.command("help"))
async def help_command(_, message):
    help_text = """
📖 **帮助信息**

**可用命令：**
• /start - 开始使用机器人
• /gen - 生成Pyrogram会话字符串
• /help - 显示此帮助信息

**使用步骤：**
1. 发送 /gen 命令
2. 输入手机号码（国际格式，如：+8613812345678）
3. 输入收到的验证码
4. 如果启用了两步验证，输入密码
5. 获取会话字符串

**注意事项：**
• 手机号码必须使用国际格式
• 验证码通常是5-6位数字
• 会话字符串非常重要，请妥善保管
• 不要将会话字符串泄露给他人

如有问题，请重新发送 /gen 开始。
    """
    await message.reply(help_text, parse_mode="markdown")

# 错误处理
@bot.on_message()
async def handle_other_messages(_, message):
    if message.text and not message.text.startswith("/"):
        user_id = message.from_user.id
        if user_id not in user_sessions:
            await message.reply("请先发送 /gen 开始生成会话字符串，或发送 /help 查看帮助。")

if __name__ == "__main__":
    logger.info("机器人启动中...")
    try:
        bot.run()
    except Exception as e:
        logger.error(f"机器人运行出错: {e}")
        raise
