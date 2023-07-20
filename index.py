import json
import logging 
import mysql.connector 
from FilmMax import FilmMax
from tmdb import route

logging.basicConfig(level=logging.CRITICAL)

# Config dosyasını yükleyin
with open("config.json", "r") as config_file:
    config = json.load(config_file)

tmdb = route.Base()
tmdb.language = "tr-TR"
tmdb.key = config["tmdb_api_key"]

mydb = mysql.connector.connect(
    host=config["db_host"],
    user=config["db_user"],
    password=config["db_password"],
    database=config["db_name"]
) 

print("------------------------------------------")
print("Merhaba, Anisu Film Scraper'a hoş geldiniz.")
print("Bazı hedef websiteleri:")
print("1 - FilmMax")
target = str(input("Lütfen bir hedef websitesi belirtin: ")) 
fetch_all_categories = input("Bütün kategorilerin filmleri çekilsin mi? (E/H): ").strip().lower() 
filmmax_scrapper = FilmMax(route=route, db=mydb, fetch_all_categories=fetch_all_categories)
print("------------------------------------------")

def getMovies(target):
    if target == "FilmMax":
        if fetch_all_categories == "e":
            return filmmax_scrapper.getAllMovies()
        else:
            return filmmax_scrapper.getMovies()
    return []

if __name__ == "__main__":
    data = getMovies(target)
    if data:
        choice = input("Film bilgileri çekildi. Bu bilgileri veritabanına yüklemek ister misiniz? (E/H): ").strip().lower()

        if choice == "e":
            # Verileri veritabanına yükle.
            filmmax_scrapper.insertMoviesToDb(data)
        else:
            choice2 = input("Anlaşıldı. Peki verileri 'movies.json' dosyasına kayıt edeyim mi? (E/H): ").strip().lower()

            if choice2 == "e":
                # Verileri json'a kayıt et
                with open("movies.json", "w", encoding="utf-8") as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
                print("Veriler 'movies.json' dosyasına kaydedildi.")
            else:
                print("Program kapatılıyor...")
    else:
        print("Belirtilen kategori için hiç film bulunamadı.")
