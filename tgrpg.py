import telebot
from telebot.types import Message
import text
import dbtg
import time
from telebot.types import InlineKeyboardButton as IB, CallbackQuery
import fight
import random
import datetime

bot = telebot.TeleBot("7055624841:AAG9OP8Yx1TeMxKLwO1KIxDW59x5rs8D1q0")

temp = {}
clear = telebot.types.ReplyKeyboardRemove()

class Enemy:
    enemy = {
        "Дракон":(100, 20),
        "Лорд":(140, 30),
        "Феникс":(80, 30),
        "Призрак":(60, 40)
    }
    def __init__(self, herolvl):
        self.name = random.choice(list(self.enemy))
        self.hp = (self.enemy[self.name][0]) + (5*(herolvl - 1))
        self.dmg = (self.enemy[self.name][1]) + (5*(herolvl - 1))

@bot.message_handler(["start"])
def start(msg:Message):
    if dbtg.check_player(msg):
        reg1(msg)
        temp[msg.chat.id] = {"name":None}
    else:
        pass

def reg1(msg:Message):
    bot.send_message(msg.chat.id, text.reg %msg.from_user.first_name)
    bot.register_next_step_handler(msg, reg2)

def reg2(msg:Message):
    if not temp[msg.chat.id]["name"]:
        temp[msg.chat.id]["name"] = msg.text
        kb = telebot.types.ReplyKeyboardMarkup(True, True)
        kb.row("Земля 🌍", "Вода 💦")
        kb.row("Огонь 🔥", "Воздух 🌬️")
        bot.send_message(msg.chat.id, "Выбери свою стихию, юный маг.", reply_markup = kb)
        bot.register_next_step_handler(msg, reg3)
    
def reg3(msg:Message):
    if msg.text == "Огонь 🔥":
        temp[msg.chat.id]["name"] = None
        bot.send_message(msg.chat.id, "Я не позволю встать тебе на сторону врага. Выбери другую стихию😡\nВведи свое имя снова")
        bot.register_next_step_handler(msg, reg2)
        return
    temp[msg.chat.id]["power"] = msg.text
    hp, dmg = fight.powers[msg.text]
    dbtg.users.write([msg.chat.id, temp[msg.chat.id]["name"], msg.text, hp, dmg, 1, 0, False])
    dbtg.heals.write([msg.chat.id, {}])
    print("Вы были успешно добавлены в базу данных")
    bot.send_message(msg.chat.id, text.tren)
    time.sleep(2)
    menu(msg)

@bot.message_handler(["menu"])
def menu(msg:Message):
    try:
        print(temp[msg.chat.id])
    except KeyError:
        temp[msg.chat.id] = {}
    bot.send_message(msg.chat.id, text.menu, reply_markup = clear)

@bot.message_handler(["square"])
def square(msg:Message):
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Тренироваться")
    kb.row("Проверить силы")
    bot.send_message(msg.chat.id, "Ты на площаде тренировок", reply_markup = kb)
    bot.register_next_step_handler(msg, square_handler)
def square_handler(msg:Message):
    if msg.text == "Тренироваться":
        workout(msg)
    elif msg.text == "Проверить силы":
        exam(msg)

@bot.message_handler(["home"])
def home(msg:Message):
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Перекусить")
    kb.row("Отдыхать")
    bot.send_message(msg.chat.id, "Ты в лагере", reply_markup = kb)
    bot.register_next_step_handler(msg, home_handler)
def home_handler(msg:Message):
    if msg.text == "Перекусить":
        eat(msg)
    elif msg.text == "Отдыхать":
        sleep(msg)

@bot.message_handler(["stats"])
def stats(msg:Message):
    player = dbtg.users.read("user_id", msg.chat.id)
    info = f"{player.power[-1]} {player.name}:\n"\
        f"Здоровье:{player.hp}❤️\n"\
        f"Урон:{player.damage}⚔️\n"\
        f"Уровень:{player.level}, {player.xp}⚜️\n"\
        f"Еда:\n"
    _,food = dbtg.heals.read("user_id", msg.chat.id)
    for i in food:
        info += f"{i} ❤️ {food[i][1]} - {food[i][0]}шт.\n"
    bot.send_message(msg.chat.id, info)
    time.sleep(1)
    menu(msg)

@bot.message_handler(["add_heal"])
def add_heal(msg:Message):
    _,food = dbtg.heals.read("user_id", msg.chat.id)
    print(food)
    food["Хлеб"] = [20, 15]
    food["Яблоко"] = [10, 25]
    dbtg.heals.write([msg.chat.id, food])
    bot.send_message(msg.chat.id, "Вам выдали еду")

def eat(msg:Message):
    kb = telebot.types.InlineKeyboardMarkup()
    _,food = dbtg.heals.read("user_id", msg.chat.id)
    if food == {}:
        bot.send_message(msg.chat.id, "У тебя нет еды", reply_markup = clear)
        menu(msg)
        return
    for i in food:
        kb.row(IB(f"{i} {food[i][1]}❤️ - {food[i][0]} шт.", callback_data = f"food_{i}_{food[i][1]}"))
    bot.send_message(msg.chat.id, "Что предпочтешь сьесть?", reply_markup = kb)

@bot.callback_query_handler(func = lambda call:True)
def callback(call:CallbackQuery):
    print(call.data)
    if call.data.startswith("food_"):
        a = call.data.split("_")
        eating(call.message, a[1], a[2])
        kb = telebot.types.InlineKeyboardMarkup()
        _,food = dbtg.heals.read("user_id", call.message.chat.id)
        for i in food:
            kb.row(IB(f"{i} {food[i][1]}❤️ - {food[i][0]} шт.", callback_data = f"food_{i}_{food[i][1]}"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup = kb)
    if call.data.startswith("sleep_"):
        a = call.data.split("_")
        if a[1] == "0":
            bot.send_message(call.message.chat.id, "Ты решил не ложиться спать")
            menu(call.message)
        else:    
            t = int(a[1]) // 2
            bot.send_message(call.message.chat.id, f"Ты лег отдыхать на {t} минут")
            time.sleep(t*2) #Вместо двойки поставить шестьдесят
            fight.sleeping(call.message, a[1])
            bot.delete_message(call.message.chat.id, call.message.message_id)
            menu(call.message)
    if call.data == "menu":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)
    if call.data == "workout":
        player = dbtg.users.read("user_id", call.message.chat.id)
        player[4] += player[5] / 10
        player[4] = round(player[4], 2)
        dbtg.users.write(player)
        bot.answer_callback_query(call.id, f"Ты тренируешься и твоя сила увеличивается\nТеперь ты наносишь {player[4]}⚔️", False)
def eating(msg, fd, hp):
    _,food = dbtg.heals.read("user_id", msg.chat.id)
    player = dbtg.users.read("user_id", msg.chat.id)
    if food[fd][0] == 1:
        del food[fd]
    else:
        food[fd][0] -= 1
    dbtg.heals.write([msg.chat.id, food])
    player[3] += int(hp)
    dbtg.users.write(player)
    print("Игрок поел")

def sleep(msg:Message):
    player = dbtg.users.read("user_id", msg.chat.id)
    low = int(fight.powers[player[2]][0] * player[5]) // 2 - player[3]
    high = int(fight.powers[player[2]][0] * player[5]) - player[3]
    kb = telebot.types.InlineKeyboardMarkup()
    if low > 0:
        kb.row(IB(f"Вздремнуть - +{low}❤️", callback_data = f"sleep_{low}"))
    if high > 0:
        kb.row(IB(f"Поспать - +{high}❤️", callback_data = f"sleep_{high}"))
    if len(kb.keyboard) == 0:
        kb.row(IB("Ты не хочешь спать", callback_data = "sleep_0"))
    bot.send_message(msg.chat.id, "Сколько будешь отдыхать?😴", reply_markup = kb)

def workout(msg:Message):
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(IB("Тренироваться", callback_data = "workout"))
    kb.row(IB("Назад", callback_data = "menu"))
    bot.send_message(msg.chat.id, "Нажимай чтобы тренироваться", reply_markup = kb)

def exam(msg:Message):
    player = dbtg.users.read("user_id", msg.chat.id)
    bot.send_message(msg.chat.id, f"Приготовься к испытанию {player[1]}", reply_markup = clear)
    time.sleep(2)
    temp[msg.chat.id]["exams"] = 0
    start_exam(msg)

def start_exam(msg:Message):
    a=random.randint(1,6)
    if a in range(1,4):
        block(msg)
    else:
        attack(msg)

def block(msg:Message):
    ydar = ("Слева", "Справа", "Сверху", "Снизу")
    random.shuffle(ydar)
    kb = telebot.types.ReplyKeyboardMarkup(True, False)
    kb.row(ydar[0], ydar[1])
    kb.row(ydar[2], ydar[3])
    ydar2 = random.choice(ydar)
    bot.send_message(msg.chat.id, f"Защищайся от удара {ydar2}", reply_markup = kb)
    temp[msg.chat.id]["blockstart"] = datetime.datetime.now().timestamp()
    bot.register_next_step_handler(msg, block_handler, ydar2)

def block_handler(msg:Message, ydar):
    final = datetime.datetime.now().timestamp()
    player = dbtg.users.read("user_id", msg.chat.id)
    if final - temp[msg.chat.id]["blockstart"] > player.damage / 10 or ydar != msg.text:
        bot.send_message(msg.chat.id, "Твоя реакцию слишком медленная, ты не успел отразить удар противника")
        time.sleep(4)
        menu(msg)
        return
    bot.send_message(msg.chat.id, "Ты отразил удар")
    start_exam(msg)

def attack(msg:Message):
    ydar = ("Слева", "Справа", "Сверху", "Снизу")
    random.shuffle(ydar)
    kb = telebot.types.ReplyKeyboardMarkup(True, False)
    kb.row(ydar[0], ydar[1])
    kb.row(ydar[2], ydar[3])
    bot.send_message(msg.chat.id, "Выбирай куда атаковать", reply_markup = kb)
    bot.register_next_step_handler(msg, attack_handler)

def attack_handler(msg:Message):
    ydar = ("Слева", "Справа", "Сверху", "Снизу")
    choise = random.choice(ydar)
    if choise == msg.text or msg.text not in ydar:
        bot.send_message(msg.chat.id, "Твоя реакцию слишком медленная, ты не смог нанести удар противнику")
        time.sleep(4)
        menu(msg)
        return
    if temp[msg.chat.id]["exam"] < 5:
        temp[msg.chat.id]["exam"] += 1
        bot.send_message(msg.chat.id, "Ты смог нанести удар противнику, продолжай в том же духе")
        start_exam(msg)
    else:
        bot.send_message(msg.chat.id, "Ты прошел испытание\nТеперь ты можешь отправляться защищать город")
        player = dbtg.users.read("user_id", msg.chat.id)
        player[7] = True
        dbtg.users.write(player)

def fight1(msg:Message):
    bot.send_message(msg.chat.id, "Ты отправился за пределы замка")
    time.sleep(3)
    bot.send_message(msg.chat.id, "Кажется враг уже близко...")
    time.sleep(1)
    newenemy()

def newenemy(msg:Message):
    readble = dbtg.users.read("name_id", msg.chat.id)
    enemy = Enemy(readble[5])
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Сразиться")
    kb.row("Сбежать")
    kb.row("Уйти в город")
    text = f"Ты встретил врага:{enemy.name}, hp={enemy.hp}, dmg={enemy.dmg}"
    bot.send_message(msg.chat.id, text, reply_markup = kb)
    bot.register_next_step_handler(msg, fight_handler, enemy)

def fight_handler(msg:Message, enemy:Enemy):
    if msg.text == "Сразиться":
        srazenie(msg, enemy)
    elif msg.text == "Сбежать":
        rand = random.randint(1,5)
        if rand in range(1,4):
            bot.send_message(msg.chat.id, "Вы сбежали")
            time.sleep(2)
            newenemy(msg)
        else:
            bot.send_message(msg.chat.id, "У вас не получилось сбежать")
            srazenie(msg, enemy)
    elif msg.text == "Уйти в город":
        time.sleep(1)
        bot.send_message(msg.chat.id, "Ты выдвинулся в город")
        time.sleep(3)
        menu(msg)

def srazenie(msg:Message, enemy:Enemy):
    ydar = player_attack(msg, enemy)
    if ydar is True:
        ydar = enemy_attack(msg, enemy) 
        if ydar is True:
            srazenie(msg, enemy)
    else:
        player = dbtg.users.read("name_id", msg.chat.id)
        time.sleep(2)
        xp = random.randint(25, 40)
        bot.send_message(msg.chat.id, f"За этот бой ты получил {xp} опыта")
        player[6] += xp
        dbtg.users.write(player)
        opit(msg)
        bot.send_message(msg.chat.id, "Ты в поисках нового противника...")
        time.sleep(2)
        newenemy(msg)
        return
    
def player_attack(msg:Message, enemy:Enemy):
    time.sleep(3)
    player = dbtg.users.read("name_id", msg.chat.id)
    enemy.hp -+ player[4]
    if enemy.hp <= 0:
        bot.send_message(msg.chat.id, "Ты победил врага")
        return False
    else:
        bot.send_message(msg.chat.id, f"{enemy.name}, xp {round(enemy.hp,1)}")
        return True
    
def enemy_attack(msg:Message, enemy:Enemy):
    time.sleep(3)
    player = dbtg.users.read("name_id", msg.chat.id)
    player[3] -= enemy.dmg
    dbtg.users.write(player)
    if player[3] <= 0:
        player[3] = 1
        dbtg.users.write(player)
        bot.send_message(msg.chat.id, "Ты получил сокрушительный удар, но тебя заметил лесник и отправил тебя обратно в лагерь. Тебе повезло новичок...")
        time.sleep(3)
        menu(msg)
        return
    else:
        bot.send_message(msg.chat.id, f"{player[1]}, xp {round(player[3],1)}")
        return True
    
def opit(msg:Message):
    player = dbtg.users.read("name_id", msg.chat.id)
    if player[6] >= 100 + ((player[5] - 1) * 50):
        player[6] -= 100 + ((player[5] - 1) * 50) 
        player[3] = fight.powers[player[2]][0] + ((player[5] - 1) * 15)
        player[5] += 1
        player[4] += 5
        player[3] += 15
        dbtg.users.write(player)
        t = f"Стихия: {player[2]}\nНикнейм: {player[1]}\n" \
            f"Здоровье: {player[3]}❤️\n" \
            f"Урон: {player[4]}⚔️\n" \
            f"Уровень: {player[5]}\nОпыт: {player[6]}⚜️"
        bot.send_message(msg.chat.id, f"Поздравляем в повышением уровня, вот твои характеристики \n" + t)
        time.sleep(2)
        return
    return

bot.infinity_polling()