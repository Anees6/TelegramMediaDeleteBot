# --- TELEGRAM BOT SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = "8673412670:AAGd09Zfk-RSY83drPF01ZJqniJkrLWDJh4"

# പഴയ മെസ്സേജുകളുടെ ഐഡി സൂക്ഷിക്കാനുള്ള ഗ്ലോബൽ വേരിയബിളുകൾ
last_warning_message_id = {} # {chat_id: message_id}