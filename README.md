# movie-data-scrapper

## Projenin Amacı
Projenin amacı belirtilen websitelerinin belirtilen kategorilerinde istediğiniz gibi Film verilerini çekebilmenizdir.
Bu servisi ücretsiz vermemin sebebi etrafta çok fazla kaçak film yayınlama sitesi olduğundan dolayıdır.
 
## Desteklenen Websiteleri:
- [filmmax.org](https://filmmax.org)

### Kurulum
- Öncelikle [mysql](https://dev.mysql.com/downloads/mysql/)'i bilgisayarınıza kurun.
   - Eğer web versiyonunu kurduysanız yanına xampp kurun, ardından mysql ve phpMyAdmin'i başlatın.
- Ardından aşağıda belirttiğim tablo kurma kodunu kullanın. bu size film tablosunu kurmanıza yarayacak.
- Ardından eğer bilgisayarınızda [Python(https://www.python.org/) yoksa kurun.
- Ardından kodu bilgisayarınıza indirin.
- Ardından konsola aşağıdaki komutu yazın.
```python
pip install -r requirements.txt
```
- Ardından aşağıdaki komutu kullanarak terminal yoluyla desteklenen websitelerinden filmleri çekebilirsiniz.
```python
python index.py
```

### Film Tablosu Oluşturma
Aşağıdaki sql komutunu çalıştırırsanız tablonuz oluşturulacaktır.
```sql
CREATE TABLE Film (
 film_id INT AUTO_INCREMENT PRIMARY KEY;
 film_adi varchar(300) 
 film_kategoriler json 
 film_yuklemeler json 
 film_yayin_tarihi date 
 film_eklenme_tarihi timestamp 
 film_aciklamasi varchar(1000)
)
```

Eklenmesini istediğiniz websiteleri varsa pull request açarak belirtebilirsiniz.

- A.Ö
