import pygame
import random
import sys
import random
import mysql.connector
import hashlib


# Připojení k MySQL databázi
def connect_db():
    return mysql.connector.connect(
        host="dbs.spskladno.cz",  # Školní server
        user="student14",           # Školní uživatelské jméno
        password="spsnet",        # Školní heslo
        database="vyuka14"        # Název databáze
    )

# Funkce pro hashování hesla
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Funkce pro registraci uživatele
def register_user(username, password):
    """ Registruje uživatele a nastaví mu počáteční hodnoty (balance, days_in_game). """
    if not username or not password:
        print("⚠️ Chyba: Uživatelské jméno a heslo nesmí být prázdné!")
        return False  

    try:
        print(f"🛠️ Pokus o registraci: '{username}'")  # Debug výpis
        db = connect_db()
        if db is None:
            print("Chyba: Připojení k databázi selhalo!")
            return False
        
        cursor = db.cursor()

        hashed_password = hash_password(password)

        # ✅ Opravený dotaz – přidán výpis všech uživatelů
        cursor.execute("SELECT username FROM betlandia_users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        print(f"🔎 Hledaný uživatel: '{username}'")
        print(f"📜 Výsledek dotazu: {existing_user}")  # <--- Přidán výpis existujícího uživatele

        if existing_user:
            print(f"Uživatelské jméno '{username}' už existuje!")
            cursor.close()
            db.close()
            return False  

        # ✅ Pokud uživatel neexistuje, registrujeme ho
        cursor.execute(
            "INSERT INTO betlandia_users (username, password, balance, days_in_game) VALUES (%s, %s, %s, %s)", 
            (username, hashed_password, 15, 1)
        )
        db.commit()
        print(f"Úspěšná registrace: {username}")

        # ✅ Ověření, zda byl uživatel přidán
        cursor.execute("SELECT * FROM betlandia_users WHERE username = %s", (username,))
        user_after_insert = cursor.fetchone()
        print(f"📌 Ověření po registraci: {user_after_insert}")  # Ověříme, zda uživatel byl opravdu přidán

        cursor.close()
        db.close()
        return True  

    except mysql.connector.Error as err:
        print(f"Chyba při registraci: {err}")  # Debug - ukáže přesnou chybu
        return False




# Funkce pro přihlášení uživatele
# Funkce pro přihlášení uživatele a načtení jeho stavu
def login_user(username, password):
    """ Přihlásí uživatele, ověří heslo a načte uložený stav. """
    global user_balance, days_in_game, logged_in_user  

    try:
        print(f"🛠️ Pokus o přihlášení: {username}")  # Debug výpis
        db = connect_db()
        cursor = db.cursor()

        hashed_password = hash_password(password)

        # ✅ Opravený dotaz – přidán výpis
        cursor.execute("SELECT username FROM betlandia_users WHERE username = %s AND password = %s", (username, hashed_password))
        user = cursor.fetchone()
        
        print(f"🔎 Výsledek hledání uživatele: {user}")  # Debug

        cursor.close()
        db.close()

        if user:
            print(f"Přihlášen uživatel: {username}")
            logged_in_user = username
            load_progress(username)
            return True
        else:
            print(f"Neúspěšné přihlášení: {username}")
            return False

    except mysql.connector.Error as err:
        print(f"Chyba při přihlášení: {err}")  # Debug výpis
        return False



# Funkce pro uložení stavu hráče do databáze
# Funkce pro uložení stavu uživatele do databáze
def save_progress(username, balance, days):
    """ Uloží stav hráče do databáze. """
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("UPDATE betlandia_users SET balance = %s, days_in_game = %s WHERE username = %s",
                   (balance, days, username))
    db.commit()

    cursor.close()
    db.close()

    print(f"✅ Data uložena: {balance} $, den {days}")

# Funkce pro načtení stavu hráče z databáze
def load_progress(username):
    """ Načte uložený stav hráče (kapitál, počet dní) z databáze. """
    global user_balance, days_in_game

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT balance, days_in_game FROM betlandia_users WHERE username = %s", (username,))
    result = cursor.fetchone()

    if result:
        user_balance, days_in_game = result  # Načteme hodnoty z databáze
        print(f"✅ Úspěšně načteno: {user_balance} $, {days_in_game}. den")
    else:
        print("⚠️ Uživatel nenalezen, nastavujeme výchozí hodnoty.")
        user_balance = starting_capital
        days_in_game = 1

    cursor.close()
    db.close()


# Inicializace Pygame
pygame.init()

# Rozměry obrazovky
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Sázení na zápasy")

# Barvy
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
DARK_GRAY = (100, 100, 100)
LIGHT_GRAY = (211, 211, 211)
BLUE = (0, 102, 204)
YELLOW = (255, 153, 51) 
GREEN = (50,250,50)

logged_in_user = None  # Proměnná pro aktuálně přihlášeného uživatele

active_bets = {}
total_bets = {}
# Počet dní ve hře
days_in_game = 1  # Začínáme od prvního dne


 # Celkově vsazené peníze

 
# Fonty
title_font = pygame.font.Font(None, 60)
small_font = pygame.font.Font(None, 30)
large_font = pygame.font.Font(None, 50)
big_font =  pygame.font.Font(None, 200)

# Základní kapitál
starting_capital = 15
user_balance = starting_capital

# Funkce pro vykreslení tlačítka
def draw_button(surface, rect, text, font, bg_color, text_color, shadow_color=None):
    if shadow_color:
        shadow_rect = rect.move(5, 5)
        pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=10)
    pygame.draw.rect(surface, bg_color, rect, border_radius=10)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

# Funkce pro gradientní text
def draw_gradient_text(surface, text, font, start_color, end_color, position):
    text_surface = font.render(text, True, start_color)
    width, height = text_surface.get_size()
    gradient_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    for y in range(height):
        r = start_color[0] + (end_color[0] - start_color[0]) * y // height
        g = start_color[1] + (end_color[1] - start_color[1]) * y // height
        b = start_color[2] + (end_color[2] - start_color[2]) * y // height
        pygame.draw.line(gradient_surface, (r, g, b), (0, y), (width, y))

    text_surface.blit(gradient_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(text_surface, text_surface.get_rect(center=position))

# Data týmů NHL s kvalitou
nhl_teams = [
    {"name": "Anaheim Ducks", "logo": "anaheim_ducks.png", "quality": 70,},
    {"name": "Arizona Coyotes", "logo": "arizona_coyotes.png", "quality": 60, "info": "Arizona Coyotes are a team from Arizona with a tough defense."},
    {"name": "Boston Bruins", "logo": "Boston_Bruins.png", "quality": 85, "info": "Boston Bruins are known for their aggressive play and strong roster."},
    {"name": "Buffalo Sabres", "logo": "Buffalo_Sabres_Logo.png", "quality": 75, "info": "Buffalo Sabres are a solid team in the Eastern Conference."},
    {"name": "Calgary Flames", "logo": "Calgary_Flames_logo.svg.png", "quality": 80, "info": "Calgary Flames are a strong Canadian team."},
    {"name": "Carolina Hurricanes", "logo": "Carolina_Hurricanes.svg.png", "quality": 90, "info": "Carolina Hurricanes are known for their strong defensive play."},
    {"name": "Chicago Blackhawks", "logo": "chicago.png", "quality": 50, "info": "Chicago Blackhawks have a rich history in the NHL."},
    {"name": "Colorado Avalanche", "logo": "Colorado_Avalanche_logo.svg.png", "quality": 95, "info": "Colorado Avalanche patří mezi špičku ligy. Díky své vysoce hodnocené soupisce jsou známí svými výkony a schopností dominovat na ledě. Jsou jedním z nejlepších týmů v NHL."},
    {"name": "Columbus Blue Jackets", "logo": "Columbus_Blue_Jackets_logo.svg.png", "quality": 65, "info": "Columbus Blue Jackets are known for their physicality."},
    {"name": "Dallas Stars", "logo": "Dallas_Stars_logo_(2013).svg.png", "quality": 80, "info": "Dallas Stars are a competitive team with great offensive power."},
    {"name": "Detroit Red Wings", "logo": "Detroit_Red_Wings_logo.svg.png", "quality": 75, "info": "Detroit Red Wings are one of the most successful franchises."},
    {"name": "Edmonton Oilers", "logo": "Logo_Edmonton_Oilers.svg.png", "quality": 90, "info": "Edmonton Oilers have stars like Connor McDavid."},
    {"name": "Florida Panthers", "logo": "Florida_Panthers_2016_logo.svg.png", "quality": 85, "info": "Florida Panthers are a strong contender in the Eastern Conference."},
    {"name": "Los Angeles Kings", "logo": "Los_Angeles_Kings_2024_Logo.svg.png", "quality": 80, "info": "Los Angeles Kings are a team with great playoff experience."},
    {"name": "Minnesota Wild", "logo": "Minnesota_Wild.svg.png", "quality": 70, "info": "Minnesota Wild are a tough team in the Western Conference."},
    {"name": "Montreal Canadiens", "logo": "Montreal_Canadiens.svg.png", "quality": 60, "info": "Montreal Canadiens are a historic and proud franchise."},
    {"name": "Nashville Predators", "logo": "Nashville_Predators_Logo_(2011).svg.png", "quality": 75, "info": "Nashville Predators are a fast and aggressive team."},
    {"name": "New Jersey Devils", "logo": "New_Jersey_Devils_logo.svg.png", "quality": 85, "info": "New Jersey Devils are a hard-working team with strong defense."},
    {"name": "New York Islanders", "logo": "Logo_New_York_Islanders.svg.png", "quality": 70, "info": "New York Islanders are known for their defensive style of play."},
    {"name": "New York Rangers", "logo": "New_York_Rangers.svg.png", "quality": 80, "info": "New York Rangers are a skilled and aggressive team."},
    {"name": "Ottawa Senators", "logo": "Ottawa_Senators_2020-2021_logo.svg.png", "quality": 60, "info": "Ottawa Senators are in a rebuilding phase, but have great potential."},
    {"name": "Philadelphia Flyers", "logo": "Philadelphia_Flyers.svg.png", "quality": 65, "info": "Philadelphia Flyers are known for their tough physical play."},
    {"name": "Pittsburgh Penguins", "logo": "Pittsburgh_Penguins_logo_(2016).svg.png", "quality": 85, "info": "Pittsburgh Penguins have stars like Sidney Crosby and Evgeni Malkin."},
    {"name": "San Jose Sharks", "logo": "SanJoseSharksLogo.svg.png", "quality": 50, "info": "San Jose Sharks are known for their playoff appearances."},
    {"name": "Seattle Kraken", "logo": "Seattle_Kraken_official_logo.svg.png", "quality": 70, "info": "Seattle Kraken are a new but promising team."},
    {"name": "St. Louis Blues", "logo": "St._Louis_Blues_logo.svg.png", "quality": 75, "info": "St. Louis Blues are strong competitors in the Western Conference."},
    {"name": "Tampa Bay Lightning", "logo": "Tampa-Bay-Lightning-Logo.png", "quality": 90, "info": "Tampa Bay Lightning jsou silným týmem s vynikajícími výkony v posledních sezónách. Mají zkušený tým, který dokáže hrát pod tlakem a jsou stále jedním z favoritů na zisk Stanley Cupu."},
    {"name": "Toronto Maple Leafs", "logo": "Toronto_Maple_Leafs_2016_logo.svg.png", "quality": 85, "info": "Toronto Maple Leafs have a passionate fanbase and a great team."},
    {"name": "Vancouver Canucks", "logo": "Vancouver_Canucks_logo.svg.png", "quality": 65, "info": "Vancouver Canucks are a young team with a lot of potential."},
    {"name": "Vegas Golden Knights", "logo": "Vegas_Golden_Knights_logo.svg.png", "quality": 90, "info": "Vegas Golden Knights are one of the top contenders in the NHL."},
    {"name": "Washington Capitals", "logo": "Washington_Capitals.svg.png", "quality": 80, "info": "Washington Capitals have a legendary player, Alexander Ovechkin."},
    {"name": "Winnipeg Jets", "logo": "Winnipeg_Jets_Logo_2011.svg.png", "quality": 75, "info": "Winnipeg Jets have a solid roster and are a strong playoff contender."},
]


def draw_league_selection():
    # Výpočet středu obrazovky a umístění tlačítek
    center_x = WIDTH // 1
    button_width, button_height = 180, 50
    spacing = 2  # Mezera mezi tlačítky

    # Vytvoření tlačítek
    nhl_button = pygame.Rect(center_x - button_width - spacing, 10, button_width, button_height)

    # Vykreslení tlačítek
  
   
    # Text na tlačítkách
    
  

    return {'NHL': nhl_button}


# Načtení pozadí
# Načtení obrázků na pozadí
# Načtení a přizpůsobení obrázků na pozadí
try:
    main_menu_bg = pygame.image.load("pozadi10.webp")
    game_bg = pygame.image.load("pozadi10.webp")

    # Přizpůsobení velikosti obrázků
    main_menu_bg = pygame.transform.scale(main_menu_bg, (WIDTH, HEIGHT))
    game_bg = pygame.transform.scale(game_bg, (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"Chyba při načítání obrázku: {e}")
    main_menu_bg = pygame.Surface(screen.get_size())
    game_bg = pygame.Surface(screen.get_size())
    main_menu_bg.fill((0, 0, 255))  # Náhradní modré pozadí
    game_bg.fill((0, 0, 255))       # Náhradní modré pozadí


# Funkce pro generování kurzů na základě kvality
def calculate_odds(team1_quality, team2_quality):
    team1_odds = round((team2_quality / team1_quality) * 2, 2)
    team2_odds = round((team1_quality / team2_quality) * 2, 2)
    return team1_odds, team2_odds

# Funkce pro generování zápasů
# Funkce pro generování zápasů
# Funkce pro generování zápasů
def generate_matches(teams):
    matches = []
    min_games = 1
    max_games = 7
    num_matches = random.randint(min_games, max_games)
    selected_teams = random.sample(teams, min(len(teams), num_matches * 2))

    for i in range(0, len(selected_teams), 2):
        if i + 1 < len(selected_teams):
            team1 = selected_teams[i]
            team2 = selected_teams[i + 1]
            # Přidáme fluktuaci ke kvalitě každého týmu
            fluctuated_quality1 = team1["quality"] + random.randint(-5, 5)
            fluctuated_quality2 = team2["quality"] + random.randint(-5, 5)
            team1_odds, team2_odds = calculate_odds(fluctuated_quality1, fluctuated_quality2)
            matches.append({
                "team1": team1,
                "team2": team2,
                "team1_odds": team1_odds,
                "team2_odds": team2_odds,
                "result": None
            })

    return matches

def handle_events(event, match_positions, bet_values, user_balance):
    global total_bets

    for item in match_positions:
        if isinstance(item[1], pygame.Rect) and item[1].collidepoint(event.pos):  # 🔥 Detekce kliknutí
            index, option = item[2], item[3]  # 📌 Každé tlačítko má index zápasu a možnost sázky
            key = (index, option)  # Unikátní identifikátor sázky

            if item[0] == "expand":
                pass  # Rozbalení funguje správně
            
            elif item[0] == "decrease":  # 🔽 Kliknutí na "-"
                if bet_values.get(key, 0) > 0:  # ✅ Sázka nesmí jít do minusu
                    bet_values[key] -= 1  
                    print(f"➖ Snížená sázka: {bet_values[key]} $ na {option}")

            elif item[0] == "increase":  # 🔼 Kliknutí na "+"
                if bet_values.get(key, 0) < user_balance:  # ✅ Nemůžeš vsadit víc, než máš
                    bet_values[key] += 1  
                    print(f"➕ Zvýšená sázka: {bet_values[key]} $ na {option}")

            elif item[0] == "confirm":  # 💰 Kliknutí na "Vsadit"
                bet_amount = bet_values.get(key, 0)
                if bet_amount > 0 and bet_amount <= user_balance:
                    user_balance -= bet_amount
                    total_bets += bet_amount  
                    active_bets[key] = (bet_amount, item[4])  # Uložíme částku a kurz
                    bet_values[key] = 0  # Reset hodnoty sázky po potvrzení
                    print(f"✅ Sázka {bet_amount} $ na {option} potvrzena!")

    return user_balance  # ✅ Vracíme upravený stav kapitálu


def draw_matches(matches, y_offset, expanded_match, user_balance, bet_values):
    total_y_offset = y_offset
    match_positions = []

    # Zobrazení zůstatku uživatele
    balance_text = large_font.render(f"Kapitál: ${user_balance}", True, WHITE)
    screen.blit(balance_text, (20, 20))

    # Nový řádek: Zobrazení celkové vsazené částky
    total_bets = sum(bet_values.values())
    bets_text = large_font.render(f"Vsazeno: ${total_bets}", True, WHITE)
    screen.blit(bets_text, (20, 60))

    for index, match in enumerate(matches):
        team1 = match["team1"]
        team2 = match["team2"]

        # Načtení a zmenšení log týmů
        try:
            logo1 = pygame.image.load(team1["logo"])
            logo1 = pygame.transform.smoothscale(logo1, (50, 50))
        except:
            logo1 = pygame.Surface((50, 50))
            logo1.fill(GRAY)

        try:
            logo2 = pygame.image.load(team2["logo"])
            logo2 = pygame.transform.smoothscale(logo2, (50, 50))
        except:
            logo2 = pygame.Surface((50, 50))
            logo2.fill(GRAY)

        # Dynamická výška tabulky
        if expanded_match == index:
            match_height = 100 + 40 * 5
        else:
            match_height = 100

        # Vykreslení šedé tabulky
        match_rect = pygame.Rect(WIDTH // 2 - 450, total_y_offset, 900, match_height)
        pygame.draw.rect(screen, (30, 30, 30), match_rect)
        pygame.draw.rect(screen, YELLOW, match_rect, 2)

        # Vertikální zarovnání log a textů
        center_y = total_y_offset + 50

        # Levý tým (logo + název)
        logo1_x = match_rect.x + 150
        screen.blit(logo1, (logo1_x, center_y - logo1.get_height() // 2))

        team1_name = small_font.render(f"{team1['name']}", True, YELLOW)
        name1_x = logo1_x + (logo1.get_width() // 2) - (team1_name.get_width() // 2)
        screen.blit(team1_name, (name1_x, center_y + 30))

        # Zobrazení kurzu pro tým 1
        team1_odds_text = small_font.render(f"({match['team1_odds']})", True, WHITE)
        screen.blit(team1_odds_text, (name1_x + team1_name.get_width() + 10, center_y + 30))

        # Pravý tým (logo + název)
        logo2_x = match_rect.right - 250
        screen.blit(logo2, (logo2_x, center_y - logo2.get_height() // 2))

        team2_name = small_font.render(f"{team2['name']}", True, YELLOW)
        name2_x = logo2_x + (logo2.get_width() // 2) - (team2_name.get_width() // 2)
        screen.blit(team2_name, (name2_x, center_y + 30))

        # Zobrazení kurzu pro tým 2
        team2_odds_text = small_font.render(f"({match['team2_odds']})", True, WHITE)
        screen.blit(team2_odds_text, (name2_x + team2_name.get_width() + 10, center_y + 30))

        # Tlačítko pro rozbalení možností
        expand_button = pygame.Rect(match_rect.centerx - 15, center_y - 15, 33, 30)
        pygame.draw.rect(screen, YELLOW if expanded_match == index else RED, expand_button)
        arrow = "0" if expanded_match == index else "V"
        arrow_text = small_font.render(arrow, True, WHITE)
        screen.blit(arrow_text, (expand_button.x + 10, expand_button.y + 5))

        match_positions.append(("expand", expand_button, index))

        if expanded_match == index:
            line_y = total_y_offset + 100
            pygame.draw.line(screen, YELLOW, (match_rect.x, line_y), (match_rect.right, line_y), 2)

            bet_options = [
                ("Výhra domácího týmu", match["team1_odds"]),
                ("Výhra hostujícího týmu", match["team2_odds"]),
                ("Remíza(3.0)", 3.0),  # Fiktivní kurz pro remízu
            ]
            option_y = line_y + 10
            for option, odds in bet_options:
                option_text = small_font.render(option, True, WHITE)
                screen.blit(option_text, (match_rect.x + 20, option_y))

                # **Užší pole pro zadání sázky** (šířka 50)
                input_box = pygame.Rect(match_rect.x + 300, option_y, 50, 30)
                pygame.draw.rect(screen, WHITE, input_box)
                pygame.draw.rect(screen, BLACK, input_box, 2)

                # Zobrazení hodnoty sázky uvnitř pole
                key = (index, option)
                bet_value = bet_values.get(key, 0)
                bet_value_text = small_font.render(str(bet_value), True, BLACK)
                screen.blit(bet_value_text, (input_box.x + 10, input_box.y + 5))

                match_positions.append(("input", input_box, index, option))

                # Tlačítka pro změnu hodnoty sázky
                decrease_button = pygame.Rect(input_box.x - 30, option_y, 30, 30)
                increase_button = pygame.Rect(input_box.right, option_y, 30, 30)
                pygame.draw.rect(screen, DARK_GRAY, decrease_button)
                pygame.draw.rect(screen, DARK_GRAY, increase_button)

                decrease_text = small_font.render("-", True, WHITE)
                increase_text = small_font.render("+", True, WHITE)
                screen.blit(decrease_text, (decrease_button.x + 10, decrease_button.y + 5))
                screen.blit(increase_text, (increase_button.x + 10, increase_button.y + 5))

                match_positions.append(("decrease", decrease_button, index, option))
                match_positions.append(("increase", increase_button, index, option))

                # **Vypočítaná možná výhra**
                possible_win = round(bet_value * odds, 2)
                possible_win_text = small_font.render(f"Možná výhra: ${possible_win}", True, YELLOW)

                # **Posun textu "Možná výhra" více doleva (už neblokuje tlačítko)**
                screen.blit(possible_win_text, (input_box.right + 140, option_y + 5))

                # Tlačítko potvrzení sázky (zůstává na místě)
                confirm_button = pygame.Rect(match_rect.x + 720, option_y, 80, 30)
                pygame.draw.rect(screen, YELLOW, confirm_button)
                confirm_text = small_font.render("Vsadit", True, WHITE)
                screen.blit(confirm_text, (confirm_button.x + 5, confirm_button.y + 5))
                match_positions.append(("confirm", confirm_button, index, option))

                option_y += 40

        total_y_offset += match_height + 20

    return match_positions

# Funkce pro zobrazení zápasů
# Globální definice výchozí ligy na začátku skriptu

# Globální slovník pro ukládání zápasů obou lig
# Základní kapitál a aktuální vstup pro sázky
user_balance = 15
input_text = ""

def generate_results(matches):
    """ Vygeneruje výsledky zápasů a vyhodnotí sázky. """
    global user_balance  

    for index, match in enumerate(matches):
        team1_score = random.randint(0, int(match["team1"]["quality"] / 20))
        team2_score = random.randint(0, int(match["team2"]["quality"] / 20))
        match["result"] = f"{team1_score} - {team2_score}"  # ✅ Uložení výsledku zápasu

        # ✅ Vyhodnocení sázek
        to_remove = []  # Uchová sázky, které se mají odstranit
        for (bet_index, bet_option), (bet_amount, odds) in active_bets.items():  # ✅ Opraveno rozbalení tuple
            if bet_index == index:  # Pokud sázka patří k tomuto zápasu
                won = False

                if bet_option == "Výhra domácího týmu" and team1_score > team2_score:
                    won = True
                elif bet_option == "Výhra hostujícího týmu" and team2_score > team1_score:
                    won = True
                elif bet_option == "Remíza(3.0)" and team1_score == team2_score:
                    won = True

                if won and odds is not None:
                    win_amount = round(bet_amount * odds, 2)
                    user_balance += win_amount  # ✅ Přičtení výhry zpět do kapitálu
                    print(f"✅ Výhra! {bet_option} přinesla {win_amount} $ (sázka: {bet_amount} * kurz: {odds})")
                else:
                    print(f"❌ Prohra! {bet_option} nevyšla.")

                to_remove.append((bet_index, bet_option))  # Přidání do seznamu na odstranění

    # ✅ Odstranění vyhodnocených sázek (jinak se mohly kopírovat)
    for key in to_remove:
        del active_bets[key]


def login_screen():
    """ Přihlašovací / registrační obrazovka uživatele. """
    global logged_in_user, user_balance, days_in_game

    input_active = "username"  # Které pole je aktivní
    username_input = ""
    password_input = ""
    error_message = ""

    running = True
    while running:
        screen.fill((30, 30, 30))  # Tmavé pozadí

        # **Střed obrazovky**
        center_x, center_y = WIDTH // 2, HEIGHT // 2

        # **Nadpis** (přesunuto do středu)
        draw_gradient_text(screen, "Přihlášení do Betlandia", large_font, (250, 30, 250), (255, 69, 0), (center_x, center_y - 150))

        # **Pole pro uživatelské jméno**
        username_rect = pygame.Rect(center_x - 150, center_y - 50, 300, 50)
        pygame.draw.rect(screen, WHITE, username_rect, 2)
        username_text = small_font.render(username_input or "Uživatelské jméno", True, WHITE)
        screen.blit(username_text, (username_rect.x + 10, username_rect.y + 15))

        # **Pole pro heslo**
        password_rect = pygame.Rect(center_x - 150, center_y + 20, 300, 50)
        pygame.draw.rect(screen, WHITE, password_rect, 2)
        password_text = small_font.render("*" * len(password_input) or "Heslo", True, WHITE)
        screen.blit(password_text, (password_rect.x + 10, password_rect.y + 15))

        # **Chybová zpráva** (pokud existuje)
        if error_message:
            error_text = small_font.render(error_message, True, RED)
            screen.blit(error_text, (center_x - error_text.get_width() // 2, center_y + 80))

        # **Tlačítko Přihlásit** (zarovnáno)
        login_button = pygame.Rect(center_x - 160, center_y + 140, 150, 50)
        draw_button(screen, login_button, "Přihlásit", small_font, GREEN, WHITE)

        # **Tlačítko Registrovat** (zarovnáno)
        register_button = pygame.Rect(center_x + 10, center_y + 140, 150, 50)
        draw_button(screen, register_button, "Registrovat", small_font, BLUE, WHITE)

        # **Tlačítko Ukončit program** (nové, zarovnáno pod tlačítky)
        quit_button = pygame.Rect(center_x - 75, center_y + 210, 150, 50)
        draw_button(screen, quit_button, "Ukončit", small_font, (204, 0, 0), WHITE, shadow_color=(153, 0, 0))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if username_rect.collidepoint(event.pos):
                    input_active = "username"
                elif password_rect.collidepoint(event.pos):
                    input_active = "password"
                elif login_button.collidepoint(event.pos):
                    if login_user(username_input, password_input):
                        print(f"✅ Přihlášen jako {username_input}")
                        main_menu()  # ✅ Přepnutí do hlavního menu
                        return  
                    else:
                        error_message = "Chybné jméno nebo heslo!"
                elif register_button.collidepoint(event.pos):
                    if register_user(username_input, password_input):
                        login_user(username_input, password_input)  # Po registraci se rovnou přihlásí
                        print(f"✅ Registrován a přihlášen jako {username_input}")
                        main_menu()  # ✅ Přepnutí do hlavního menu
                        return  
                    else:
                        error_message = "Registrace selhala! Možná už existuje účet."
                elif quit_button.collidepoint(event.pos):
                    print("Program ukončen")
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.KEYDOWN:
                if input_active == "username":
                    if event.key == pygame.K_BACKSPACE:
                        username_input = username_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        input_active = "password"
                    else:
                        username_input += event.unicode
                elif input_active == "password":
                    if event.key == pygame.K_BACKSPACE:
                        password_input = password_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if login_user(username_input, password_input):
                            print(f"✅ Přihlášen jako {username_input}")
                            main_menu()  # ✅ Přepnutí do hlavního menu
                            return  
                        else:
                            error_message = "❌ Chybné jméno nebo heslo!"
                    else:
                        password_input += event.unicode


def display_matches():
    global user_balance, active_bets, matches, current_league, betting_disabled, days_in_game, logged_in_user, total_bets

    if logged_in_user is None:
        print("⚠️ Chyba: Nebyl nalezen přihlášený uživatel!")
        return  

    user_balance = starting_capital
    active_bets.clear()
    total_bets = 0  

    current_league = 'NHL'
    matches = generate_matches(nhl_teams)
    bet_values = {}  
    can_simulate = True  
    betting_disabled = False  
    next_day_enabled = False  
    expanded_match = None

    running = True
    while running:
        screen.blit(game_bg, (0, 0))

        # Zobrazení počtu dní ve hře
        days_text = large_font.render(f"{days_in_game}. den", True, WHITE)
        screen.blit(days_text, (WIDTH // 2 - days_text.get_width() // 2, 20))

        # **Rozpis zápasů**
        match_positions = draw_matches(matches, 100, expanded_match, user_balance, bet_values)

        # **Tlačítka**
        button_height = 50

        # 🛠 **Tlačítko "Menu"**
        back_button_rect = pygame.Rect(20, HEIGHT - button_height - 20, 150, button_height)
        draw_button(screen, back_button_rect, "Menu", small_font, RED, WHITE)

        # 🛠 **Tlačítko "Simulovat"**
        simulate_button_rect = pygame.Rect(WIDTH - 320, HEIGHT - button_height - 20, 150, button_height)
        simulate_button_color = GREEN if can_simulate else DARK_GRAY
        draw_button(screen, simulate_button_rect, "Simulovat", small_font, simulate_button_color, WHITE)

        # 🛠 **Tlačítko "Další den"**
        next_day_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - button_height - 20, 150, button_height)
        next_day_button_color = BLUE if next_day_enabled else DARK_GRAY
        draw_button(screen, next_day_button_rect, "Další den", small_font, next_day_button_color, WHITE)

        # ✅ **Zobrazení výsledků zápasů**
        if betting_disabled:
            for index, match in enumerate(matches):
                if match["result"]:
                    match_x = WIDTH // 2 - 450  
                    result_x = match_x + 430  
                    result_y = 100 + (index * 120) + 70  

                    result_text = small_font.render(match["result"], True, WHITE)
                    screen.blit(result_text, (result_x, result_y))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_progress(logged_in_user, user_balance, days_in_game)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(event.pos):
                    save_progress(logged_in_user, user_balance, days_in_game)
                    running = False  
                elif simulate_button_rect.collidepoint(event.pos) and can_simulate:
                    expanded_match = None  
                    bet_values.clear()  
                    generate_results(matches)  # ✅ Aktualizujeme zápasy se skóre
                    can_simulate = False
                    betting_disabled = True
                    next_day_enabled = True
                elif next_day_button_rect.collidepoint(event.pos) and next_day_enabled:
                    matches = generate_matches(nhl_teams)
                    can_simulate = True
                    betting_disabled = False
                    next_day_enabled = False
                    days_in_game += 1
                    save_progress(logged_in_user, user_balance, days_in_game)
                else:
                    if not betting_disabled:
                        for item in match_positions:
                            if isinstance(item[1], pygame.Rect) and item[1].collidepoint(event.pos):
                                if item[0] == "expand":
                                    if expanded_match is not None and expanded_match != item[2]:
                                        bet_values.clear()  
                                    expanded_match = item[2] if expanded_match != item[2] else None
                                elif item[0] == "increase":
                                    index, option = item[2], item[3]
                                    key = (index, option)
                                    if bet_values.get(key, 0) < user_balance:
                                        bet_values[key] = bet_values.get(key, 0) + 1
                                        print(f"➕ Zvýšená sázka: {bet_values[key]} $ na {option}")
                                elif item[0] == "decrease":
                                    index, option = item[2], item[3]
                                    key = (index, option)
                                    if bet_values.get(key, 0) > 0:
                                        bet_values[key] -= 1
                                        print(f"➖ Snížená sázka: {bet_values[key]} $ na {option}")
                                elif item[0] == "confirm":
                                    index, option = item[2], item[3]
                                    key = (index, option)
                                    bet_amount = bet_values.get(key, 0)

                                    # **Najdeme správný kurz podle týmu a možnosti**
                                    odds = None
                                    for match in matches:
                                        if index == matches.index(match):
                                            if option == "Výhra domácího týmu":
                                                odds = match["team1_odds"]
                                            elif option == "Výhra hostujícího týmu":
                                                odds = match["team2_odds"]
                                            elif option == "Remíza(3.0)":
                                                odds = 3.0

                                    if odds is not None and bet_amount > 0 and bet_amount <= user_balance:
                                        user_balance -= bet_amount
                                        total_bets += bet_amount  # ✅ Teď je total_bets správně inicializována
                                        active_bets[key] = (bet_amount, odds)
                                        bet_values[key] = 0  
                                        print(f"✅ Sázka {bet_amount} $ na {option} potvrzena s kurzem {odds}!")
                                    else:
                                        print(f"⚠️ Chyba při sázení: Neplatná částka nebo kurz! ({bet_amount} $, kurz: {odds})")

    main_menu()




def simulate_and_display_results(matches):
    results_surface = pygame.Surface((600, 400))
    results_surface.fill((50, 50, 50))  # Tmavě šedé pozadí pro okno výsledků
    font = pygame.font.Font(None, 30)

    # Přidání tlačítka pro zavření (posunuto více doprava a dolů)
    close_button_rect = pygame.Rect(540, 360, 50, 30)  # Posunutí dolů a doprava
    close_button_text = font.render("X", True, WHITE)

    y_offset = 50  # Začínáme 50 pixelů od horního okraje
    for match in matches:
        # Generování výsledku
        team1_score = random.randint(0, int(match["team1"]["quality"] / 20))
        team2_score = random.randint(0, int(match["team2"]["quality"] / 20))
        match["result"] = f"{match['team1']['name']} {team1_score} - {team2_score} {match['team2']['name']}"

        # Vytvoření a vykreslení textu s výsledkem
        result_text = font.render(match["result"], True, WHITE)
        results_surface.blit(result_text, (50, y_offset))
        y_offset += 40  # Posun o 40 pixelů dolů pro další zápas

    results_position = (WIDTH // 2 - 300, HEIGHT // 2 - 200)
    results_active = True

    while results_active:
        screen.blit(game_bg, (0, 0))  # Vymaže celou obrazovku
        screen.blit(results_surface, results_position)
        pygame.draw.rect(results_surface, RED, close_button_rect)  # Tlačítko zavření na tabulce
        screen.blit(close_button_text, (close_button_rect.x + 15, close_button_rect.y + 5))

        screen.blit(results_surface, results_position)  # Opětovné vykreslení okna výsledků
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Správná detekce kliknutí na tlačítko zavření
                relative_x = event.pos[0] - results_position[0]
                relative_y = event.pos[1] - results_position[1]
                if close_button_rect.collidepoint(relative_x, relative_y):
                    results_active = False  # Zavřít okno výsledků

    # Po zavření okna výsledků překreslíme hlavní obrazovku
    screen.blit(game_bg, (0, 0))
    pygame.display.flip()



def display_teams():
    running = True
    num_per_row = 7
    logo_size = 100
    padding = 150  # Zvýšené mezisloje pro lepší vizuální oddělení
    total_logo_width = num_per_row * logo_size + (num_per_row - 1) * padding
    start_x = (WIDTH - total_logo_width) // 2  # Opravdové centrování na šířku

    # Výpočet počátečního y pro centrování log na obrazovce
    num_rows = (len(nhl_teams) + num_per_row - 1) // num_per_row
    total_height = num_rows * (logo_size + 30) + (num_rows - 1) * 50  # Menší mezera mezi logy a větší mezera mezi řádky
    start_y = (HEIGHT - total_height) // 2  # Opravdové centrování na výšku

    while running:
        screen.blit(game_bg, (0, 0))

        # Tlačítko "Menu"
        menu_rect = pygame.Rect(20, HEIGHT - 70, 150, 50)
        pygame.draw.rect(screen, RED, menu_rect)
        menu_text = small_font.render("Menu", True, WHITE)
        screen.blit(menu_text, (menu_rect.x + 10, menu_rect.y + 10))

        x_start = start_x
        y_start = start_y
        count = 0

        for team in nhl_teams:
            logo_path = team["logo"]
            try:
                logo = pygame.image.load(logo_path)
                logo = pygame.transform.smoothscale(logo, (logo_size, logo_size))
            except:
                logo = pygame.Surface((logo_size, logo_size))
                logo.fill(GRAY)  # Náhradní šedé pozadí, pokud se nepodaří načíst logo

            logo_rect = pygame.Rect(x_start, y_start, logo_size, logo_size)
            screen.blit(logo, logo_rect)

            # Zobrazit název týmu pod logem
            team_name_text = small_font.render(team["name"], True, WHITE)
            text_rect = team_name_text.get_rect(center=(logo_rect.centerx, logo_rect.bottom + 20))
            screen.blit(team_name_text, text_rect)

            x_start += logo_size + padding  # Posuneme x pozici pro další logo
            count += 1
            if count % num_per_row == 0:  # Nový řádek po sedmi logách
                x_start = start_x
                y_start += logo_size + 80  # Zvětšený prostor pro text a mezeru mezi řádky

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if menu_rect.collidepoint(event.pos):
                    return  # Vrátit se do hlavního menu

# Hlavní menu
# Funkce pro získání TOP 10 hráčů z databáze
def get_top_players():
    """ Načte TOP 10 hráčů podle nejvyššího dosaženého kapitálu. """
    try:
        db = connect_db()
        cursor = db.cursor()

        # Výběr top 10 hráčů podle maximálního dosaženého kapitálu
        cursor.execute("SELECT username, MAX(balance) FROM betlandia_users GROUP BY username ORDER BY MAX(balance) DESC LIMIT 10")
        top_players = cursor.fetchall()

        cursor.close()
        db.close()
        return top_players  # Vrací seznam [(username, max_balance), ...]
    except mysql.connector.Error as err:
        print(f"❌ Chyba při načítání TOP 10 hráčů: {err}")
        return []  # V případě chyby vrátíme prázdný seznam


# Hlavní menu s tabulkou TOP 10 hráčů
def main_menu():
    global logged_in_user

    if not logged_in_user:
        login_screen()  # ✅ Nechá uživatele přihlásit se

    running = True
    while running:
        screen.blit(main_menu_bg, (0, 0))

        # Nadpis
        draw_gradient_text(screen, "BETLANDIA", big_font, (250, 30, 250), (255, 69, 0), (WIDTH // 2, HEIGHT // 5))

        # Tlačítka
        button_width, button_height = 300, 70
        bet_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - 50, button_width, button_height)
        roster_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 50, button_width, button_height)
        quit_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 150, button_width, button_height)

        draw_button(screen, bet_rect, "Sázet", large_font, (0, 153, 76), WHITE, shadow_color=(0, 102, 51))
        draw_button(screen, roster_rect, "Seznam", large_font, BLUE, WHITE)
        draw_button(screen, quit_rect, "Zpět na plochu", large_font, (204, 0, 0), WHITE, shadow_color=(153, 0, 0))

        # 🔥 **Načtení a vykreslení TOP 10 hráčů** 🔥
        top_players = get_top_players()  # Načteme hráče z databáze

        if top_players:
            top_text = large_font.render("TOP 10 HRÁČŮ", True, RED)
            screen.blit(top_text, (WIDTH - 350, HEIGHT // 5))

            # Vykreslení tabulky hráčů
            for i, (username, max_balance) in enumerate(top_players, start=1):
                player_text = small_font.render(f"{i}. {username}: ${max_balance}", True, WHITE)
                screen.blit(player_text, (WIDTH - 350, HEIGHT // 5 + 50 + i * 30))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if bet_rect.collidepoint(event.pos):
                    print("✅ Kliknuto na 'Sázet'")
                    display_matches()
                elif roster_rect.collidepoint(event.pos):
                    print("✅ Kliknuto na 'Seznam'")
                    display_teams()
                elif quit_rect.collidepoint(event.pos):
                    print("❌ Hra ukončena.")
                    running = False

if __name__ == "__main__":
    main_menu()
