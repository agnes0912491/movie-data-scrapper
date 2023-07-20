import datetime
import json
import time
import requests
import asyncio
import urllib3

from bs4 import BeautifulSoup
from tqdm import tqdm 
from omdbapi.movie_search import GetMovie, GetMovieException

urllib3.disable_warnings()

# Config dosyasını yükleyin
with open("config.json", "r") as config_file:
    config = json.load(config_file)

class FilmMax:
    def __init__(self, route, db, fetch_all_categories):
        self.movies = []
        self.categories = ["aksiyon", "aile", "animasyon", "bilim", "dram", "gerilim", "komedi", "macera", "savaş"]
        if fetch_all_categories == "h":
            self.category = int(input(f"""Lütfen bir kategori numarası seçin;
{" | ".join([f"{i} - {c}" for i, c in enumerate(self.categories)])}
"""))

        self.page = 1
        self.request_count = 0
        self.route = route 
        self.db = db
        self.cursor = self.db.cursor()
        self.omdb = GetMovie(api_key=config["omdb_api_key"])
        self.blacklisted_movies = self.load_blacklist()

    def load_blacklist(self):
        try:
            with open("blacklisted_movies.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def fetchMoviesFromPage(self, page, category):  # Accept category as a parameter
        url = f"https://filmmax.org/film-arsivi/sayfa/{page}/?cat={category}"
        request = requests.get(url, verify=False)
        time.sleep(0.1)
        soup = BeautifulSoup(request.content, 'html.parser')
        movie_list = soup.find_all("div", class_="list-movie")
        self.request_count += 1
        return [self.getMovieInfo(movie) for movie in tqdm(movie_list, desc="Filmler diziye ekleniyor...")]

    def getAllMovies(self):
        baslangic_zamani = time.time()
        all_movies = []
        for category_index, category in enumerate(self.categories):
            movies = self.getMovies(category_index)  # Pass the category_index to getMovies()
            all_movies.extend(movies)

        bitis_zamani = time.time() - baslangic_zamani
        print(" " * 100)  # Clear the progress bar
        print(f"İşlem bitti, geçen süre: {bitis_zamani:.2f} saniye")
        return all_movies

    def getMovies(self, category_index): 
        page = 1
        baslangic_zamani = time.time()
        category = self.categories[category_index]  # Get the category based on the category_index
        print(f"{category} Kategorisindeki filmlerin yüklenme işlemi başlatıldı.")

        while True:
            movies = self.fetchMoviesFromPage(page, category)  # Pass the category to fetchMoviesFromPage()

            if not movies or all(film is None for film in movies):
                break

            self.movies.extend(film for film in movies if film is not None)
            page += 1

        bitis_zamani = time.time() - baslangic_zamani
        print(" " * 100)  # Clear the progress bar
        print(f"{category} Kategorisindeki filmlerin yüklenme işlemi bitti, geçen süre: {bitis_zamani:.2f}")
        return self.movies

    def getMovieInfo(self, movie):
        title = movie.find("a", class_="movie-title").text.strip()
        poster = movie.find("div", class_="movie-img")["data-bg"]
        categories = [item.strip().replace('\u00e7', 'ç') for item in movie.find("span").text.split(",")]
        
        if "Anime" not in categories:
            new_target_url = movie.find("div", class_="img").find("a")["href"]
            new_target = requests.get(new_target_url, verify=False)
            time.sleep(0.1)
            soup2 = BeautifulSoup(new_target.content, "html.parser") 
            # Check if the "video" div exists
            video_divs = soup2.find_all("div", class_="video")
            if not video_divs:
                self.add_to_blacklist(title)
                print(f"No video iframe found for {title}. Skipping...")
                return None

            iframe_url = video_divs[0].find_all("iframe")
            if not iframe_url:
                self.add_to_blacklist(title)
                print(f"No iframe URL found for {title}. Skipping...")
                return None
            else:
                iframe_url = iframe_url[0]["src"]

            movie_info_divs = soup2.find_all("div", class_="movie-info")[0].find_all("div", class_="info")
            self.request_count += 1
 
            if len(movie_info_divs) >= 4:
                original_name = movie_info_divs[3].text.split("Orijinal İsim: ")[1]
            else:
                original_name = title

            if original_name not in self.blacklisted_movies:
                async def get_tmdb_info(name):
                    movies = await self.route.Movie().search(query=name)
                    if not movies["results"]:
                        try:
                            omdb_movies = await self.omdb.get_movie(title=name)
                            if omdb_movies:
                                print(omdb_movies)
                                return {
                                    "overview": "Overview not available",
                                    "release_date": "Release date not available",
                                }
                            else:
                                print(f"\n{name} isimli film iki veritabanında da bulunamadı.")
                                self.add_to_blacklist(name) 
                        except GetMovieException:
                            print(f"\n{name} isimli film iki veritabanında da bulunamadı.")
                            self.add_to_blacklist(name)
                    else:
                        return {
                            "overview": movies["results"][0]["overview"],
                            "release_date": movies["results"][0]["release_date"],
                        }

                data = asyncio.run(get_tmdb_info(original_name))

                if data:
                    return {
                        "title": title,
                        "thumbnailVertical": poster,
                        "categories": categories,
                        "overview": data["overview"],
                        "release_date": data["release_date"],
                        "video": iframe_url
                    }

    def add_to_blacklist(self, movie_name):
        try:
            with open("blacklisted_movies.json", "r") as f:
                blacklist = json.load(f)
        except FileNotFoundError:
            blacklist = []

        if movie_name not in blacklist:
            blacklist.append(movie_name)

        with open("blacklisted_movies.json", "w") as f:
            json.dump(blacklist, f)

    def insertMoviesToDb(self, movies):
        for movie in movies: 
            if movie and isinstance(movie, dict) and "release_date" in movie and len(movie["release_date"]) > 0:
                film_adi = movie["title"]
                film_aciklamasi = movie["overview"]
                film_kategoriler = json.dumps(movie["categories"])
                film_yuklemeler = json.dumps({"thumbnailVertical": movie["thumbnailVertical"], "video": movie["video"]})
                film_yayin_tarihi = datetime.datetime.strptime(movie["release_date"], '%Y-%m-%d')

                # Veritabanında varlık kontrolü
                self.cursor.execute("SELECT * FROM film WHERE film_adi = %s", (film_adi,))
                result = self.cursor.fetchone()
                if result:
                    print(f"{film_adi} adlı film zaten veritabanında mevcut. Ekleme yapılmadı.")
                elif film_aciklamasi is None or film_kategoriler is None or film_yuklemeler is None or film_yayin_tarihi is None:
                    print(f"{film_adi} adlı film veritabanına eklenemedi. Eksik bilgi bulunuyor.")
                else:
                    self.cursor.execute("INSERT INTO film (film_adi, film_sahip_id, film_aciklamasi, film_kategoriler, film_yuklemeler, film_yayin_tarihi) VALUES (%s, %s, %s, %s, %s, %s)", (
                        film_adi,
                        1,
                        film_aciklamasi,
                        film_kategoriler,
                        film_yuklemeler,
                        film_yayin_tarihi
                    ))
                    self.db.commit()
                    print(f"{film_adi} adlı film veritabanına başarıyla eklendi.")
            else:
                print(f"Hata: Geçersiz tarih formatı veya eksik tarih bilgisi. {movie['title']}")
                self.add_to_blacklist(movie_name=movie['title'])
