"""Katalog bahasa + metadata sumber konten tepercaya (dokumentasi resmi, Wikipedia, dll.)."""

LANGS = [
    dict(key="html", name="HTML", color="#E44D26", icon="🌐", level="Pemula", group="Web",
         tagline="Kerangka dan struktur halaman web.", wiki="HTML", so="html", dev="html", gh="language:html",
         docs_name="MDN Web Docs", docs_url="https://developer.mozilla.org/en-US/docs/Web/HTML", mdn=True),
    dict(key="css", name="CSS", color="#264DE4", icon="🎨", level="Pemula", group="Web",
         tagline="Warna, tata letak, dan tampilan halaman.", wiki="CSS", so="css", dev="css", gh="language:css",
         docs_name="MDN Web Docs", docs_url="https://developer.mozilla.org/en-US/docs/Web/CSS", mdn=True),
    dict(key="javascript", name="JavaScript", color="#F0B90B", icon="⚡", level="Pemula", group="Web",
         tagline="Membuat halaman web interaktif.", wiki="JavaScript", so="javascript", dev="javascript",
         gh="language:javascript", docs_name="MDN Web Docs",
         docs_url="https://developer.mozilla.org/en-US/docs/Web/JavaScript", mdn=True),
    dict(key="python", name="Python", color="#3776AB", icon="🐍", level="Pemula", group="Umum",
         tagline="Bahasa serbaguna: web, data, AI, otomasi.", wiki="Python (programming language)", so="python",
         dev="python", gh="language:python", docs_name="Dokumentasi Python",
         docs_url="https://docs.python.org/3/tutorial/", mdn=False),
    dict(key="sql", name="SQL", color="#00758F", icon="🗄️", level="Pemula", group="Data",
         tagline="Bahasa standar untuk mengelola basis data.", wiki="SQL", so="sql", dev="sql", gh="topic:sql",
         docs_name="PostgreSQL Docs", docs_url="https://www.postgresql.org/docs/current/sql.html", mdn=False),
    dict(key="java", name="Java", color="#E76F00", icon="☕", level="Menengah", group="Umum",
         tagline="Bahasa berorientasi objek untuk aplikasi skala besar.", wiki="Java (programming language)",
         so="java", dev="java", gh="language:java", docs_name="Oracle Java Tutorials",
         docs_url="https://docs.oracle.com/javase/tutorial/", mdn=False),
    dict(key="php", name="PHP", color="#777BB4", icon="🐘", level="Pemula", group="Web",
         tagline="Bahasa sisi server untuk membangun situs dinamis.", wiki="PHP", so="php", dev="php",
         gh="language:php", docs_name="PHP Manual", docs_url="https://www.php.net/manual/en/", mdn=False),
    dict(key="c", name="C", color="#5C6BC0", icon="🔧", level="Menengah", group="Sistem",
         tagline="Dasar pemrograman sistem dan memori.", wiki="C (programming language)", so="c", dev="c",
         gh="language:c", docs_name="cppreference (C)", docs_url="https://en.cppreference.com/w/c", mdn=False),
    dict(key="cpp", name="C++", color="#00599C", icon="⚙️", level="Menengah", group="Sistem",
         tagline="C dengan OOP dan pustaka standar yang kaya.", wiki="C++", so="c++", dev="cpp",
         gh='language:"c++"', docs_name="cppreference (C++)", docs_url="https://en.cppreference.com/w/cpp", mdn=False),
    dict(key="csharp", name="C#", color="#68217A", icon="🎯", level="Menengah", group="Umum",
         tagline="Bahasa modern untuk .NET, game (Unity), dan desktop.", wiki="C Sharp (programming language)",
         so="c#", dev="csharp", gh='language:"c#"', docs_name="Microsoft Learn (C#)",
         docs_url="https://learn.microsoft.com/en-us/dotnet/csharp/", mdn=False),
    dict(key="react", name="React", color="#0E9FBC", icon="⚛️", level="Menengah", group="Web",
         tagline="Pustaka UI berbasis komponen dari JavaScript.", wiki="React (software)", so="reactjs", dev="react",
         gh="topic:react", docs_name="react.dev", docs_url="https://react.dev/learn", mdn=False),
    dict(key="mysql", name="MySQL", color="#00618A", icon="🐬", level="Menengah", group="Data",
         tagline="Sistem basis data relasional paling populer.", wiki="MySQL", so="mysql", dev="mysql",
         gh="topic:mysql", docs_name="MySQL Reference Manual", docs_url="https://dev.mysql.com/doc/refman/8.0/en/",
         mdn=False),
]

BY_KEY = {l["key"]: l for l in LANGS}
_ALIASES = {"js": "javascript", "jquery": "javascript", "c++": "cpp", "c#": "csharp", "reactjs": "react",
            "react.js": "react", "front end": "html", "frontend": "html"}
_SUFFIXES = (" tutorial", " reference", " examples", " example", " certificate", " quiz")


def find_lang(name):
    """Cari bahasa dari nama bebas ("Python Tutorial", "JS", "jQuery", "C++"). None bila tidak ada."""
    if not name:
        return None
    n = name.strip().lower()
    for s in _SUFFIXES:
        if n.endswith(s):
            n = n[: -len(s)].strip()
    n = _ALIASES.get(n, n)
    if n in BY_KEY:
        return BY_KEY[n]
    for l in LANGS:
        if l["name"].lower() == n:
            return l
    return None


ROADMAP = [
    dict(title="Pengembang Front-End", icon="🎨", desc="Membangun tampilan web yang interaktif dan responsif.",
         steps=[("html", "Mulai dari struktur halaman."), ("css", "Percantik dan buat responsif."),
                ("javascript", "Tambahkan interaksi."), ("react", "Bangun UI berbasis komponen.")]),
    dict(title="Pengembang Back-End", icon="🛠️", desc="Membuat logika server dan menyimpan data.",
         steps=[("python", "Kuasai dasar pemrograman."), ("sql", "Kelola data dengan query."),
                ("php", "Bangun situs dinamis sisi server."), ("mysql", "Rancang basis data yang efisien.")]),
    dict(title="Rekayasa Perangkat Lunak", icon="⚙️", desc="Memahami fondasi komputer dan aplikasi skala besar.",
         steps=[("c", "Pahami memori dan pointer."), ("cpp", "Tambah OOP dan STL."),
                ("java", "Bangun aplikasi berorientasi objek."), ("csharp", "Jelajahi .NET dan game Unity.")]),
    dict(title="Data dan Otomasi", icon="📊", desc="Mengolah data dan mengotomasi pekerjaan.",
         steps=[("python", "Bahasa utama untuk data dan AI."), ("sql", "Ambil dan ringkas data."),
                ("mysql", "Kelola basis data relasional.")]),
]

INFO = {
    "tentang": dict(title="Tentang UG-Stack", sections=[
        ("Apa itu UG-Stack?", "UG-Stack adalah platform belajar pemrograman berbasis Python (Flet) yang berjalan di web dan Android. Materi pelajaran, cheat sheet, dan quiz disusun sendiri, lalu diperkaya otomatis dengan konten dari sumber tepercaya."),
        ("Sumber konten otomatis", "Wikipedia (ringkasan), MDN Web Docs (referensi web), Stack Overflow (pertanyaan terpopuler), DEV Community (artikel komunitas), dan GitHub (repositori populer). Semua diambil lewat API publik, selalu menampilkan tautan ke sumber aslinya, dan di-cache 24 jam agar tetap bisa dibuka saat offline."),
        ("Lisensi konten", "Teks dari Wikipedia, MDN, dan Stack Overflow berlisensi CC BY-SA milik penulis aslinya. UG-Stack hanya menampilkan ringkasan dan tautan, bukan menyalin artikel utuh."),
    ]),
    "komunitas": dict(title="Komunitas dan Kontak", sections=[
        ("Bergabung", "Ikuti pembaruan UG-Stack, bertanya, dan berbagi proyek bersama sesama pelajar. Tautan resmi komunitas dapat ditambahkan oleh pengelola di berkas content/languages.py."),
        ("Butuh bantuan?", "Mulai dari halaman Roadmap atau Tutorial. Untuk pertanyaan spesifik, gunakan fitur Pencarian: ia menampilkan pertanyaan terkait dari Stack Overflow."),
    ]),
    "aplikasi": dict(title="Pasang Aplikasi UG-Stack", sections=[
        ("Web", "Jalankan python main.py lalu buka http://127.0.0.1:8550 di browser. Tampilan otomatis menyesuaikan lebar layar."),
        ("Android (APK)", "Pasang Flutter SDK, JDK 17, dan Android SDK, lalu jalankan flet build apk di folder proyek. Salin berkas .apk dari folder build/apk ke HP dan pasang. Rincian ada di README."),
        ("Data di aplikasi", "Pada APK, data pengguna dan cache konten disimpan di folder khusus aplikasi sehingga tetap ada setelah aplikasi ditutup."),
    ]),
    "spaces": dict(title="Ruang Kode UG-Stack", sections=[
        ("Ruang eksperimen kode", "Gunakan Try it Editor untuk mencoba contoh kode dari setiap pelajaran. Buka pelajaran, lalu tekan tombol Try it Yourself untuk memuat kode ke editor."),
        ("Segera hadir", "Penyimpanan proyek pribadi dan berbagi tautan hasil kode."),
    ]),
}

ABOUT = {
 "html": ("HTML adalah bahasa markup standar untuk menyusun struktur halaman web: judul, paragraf, tautan, gambar, tabel, dan formulir. Browser membacanya lalu menampilkannya; CSS dan JavaScript melengkapi tampilan dan interaksinya.",
          "HTML is the standard markup language for structuring web pages: headings, paragraphs, links, images, tables, and forms. Browsers read it and render it; CSS and JavaScript add styling and interaction."),
 "css": ("CSS mengatur tampilan dokumen HTML: warna, huruf, jarak, tata letak (Flexbox dan Grid), serta penyesuaian layar lewat media query.",
         "CSS controls the presentation of HTML documents: colors, fonts, spacing, layout (Flexbox and Grid), and screen adaptation through media queries."),
 "javascript": ("JavaScript adalah bahasa pemrograman yang berjalan di browser (dan di server lewat Node.js) untuk membuat halaman web interaktif, mulai dari validasi formulir sampai aplikasi lengkap.",
                "JavaScript is a programming language that runs in the browser (and on servers through Node.js) to make web pages interactive, from form validation to full applications."),
 "python": ("Python adalah bahasa tingkat tinggi dengan sintaks yang ringkas dan mudah dibaca, dipakai untuk web, analisis data, kecerdasan buatan, otomasi, dan pendidikan.",
            "Python is a high-level language with concise, readable syntax, used for the web, data analysis, artificial intelligence, automation, and education."),
 "sql": ("SQL adalah bahasa standar untuk menyimpan, mengambil, dan mengubah data pada basis data relasional menggunakan tabel, baris, dan kolom.",
         "SQL is the standard language for storing, retrieving, and changing data in relational databases using tables, rows, and columns."),
 "java": ("Java adalah bahasa berorientasi objek yang dikompilasi menjadi bytecode dan dijalankan di JVM, sehingga programnya dapat berjalan di banyak sistem operasi.",
          "Java is an object-oriented language compiled to bytecode and run on the JVM, so its programs can run on many operating systems."),
 "php": ("PHP adalah bahasa sisi server untuk membangun situs dinamis; kodenya dijalankan di server dan menghasilkan HTML yang dikirim ke browser.",
         "PHP is a server-side language for building dynamic sites; its code runs on the server and produces HTML sent to the browser."),
 "c": ("C adalah bahasa pemrograman sistem yang dekat dengan perangkat keras, memberi kendali langsung atas memori lewat pointer, dan menjadi dasar banyak bahasa lain.",
       "C is a systems programming language close to the hardware that gives direct control over memory through pointers and underlies many other languages."),
 "cpp": ("C++ memperluas C dengan pemrograman berorientasi objek, template, dan pustaka standar (STL), banyak dipakai untuk game, sistem, dan aplikasi berkinerja tinggi.",
         "C++ extends C with object-oriented programming, templates, and the standard library (STL), widely used for games, systems, and high-performance applications."),
 "csharp": ("C# adalah bahasa modern dari Microsoft untuk platform .NET: aplikasi web, desktop, seluler, layanan cloud, dan game dengan Unity.",
            "C# is a modern language from Microsoft for the .NET platform: web, desktop, mobile, cloud services, and games with Unity."),
 "react": ("React adalah pustaka JavaScript untuk membangun antarmuka pengguna dari komponen yang dapat dipakai ulang, dengan state yang memicu tampilan ulang secara efisien.",
           "React is a JavaScript library for building user interfaces from reusable components, with state that triggers efficient re-rendering."),
 "mysql": ("MySQL adalah sistem manajemen basis data relasional sumber terbuka yang populer untuk aplikasi web, menyimpan data dalam tabel dan diakses dengan SQL.",
           "MySQL is a popular open-source relational database management system for web applications that stores data in tables and is accessed with SQL."),
}

RESOURCES = {
 "html": [("MDN: Learn HTML", "https://developer.mozilla.org/en-US/docs/Learn/HTML", "Jalur belajar HTML dari dasar sampai formulir dan tabel.", "A learning path for HTML from the basics to forms and tables."),
          ("web.dev Learn HTML", "https://web.dev/learn/html", "Kursus HTML modern dari tim Google Chrome.", "A modern HTML course from the Google Chrome team."),
          ("freeCodeCamp", "https://www.freecodecamp.org/learn", "Kurikulum gratis dengan latihan langsung.", "A free curriculum with hands-on practice.")],
 "css": [("MDN: Learn CSS", "https://developer.mozilla.org/en-US/docs/Learn/CSS", "Panduan CSS lengkap: selector, box model, layout.", "A complete CSS guide: selectors, box model, layout."),
         ("web.dev Learn CSS", "https://web.dev/learn/css", "Kursus CSS modern termasuk Flexbox dan Grid.", "A modern CSS course including Flexbox and Grid."),
         ("CSS-Tricks: Flexbox Guide", "https://css-tricks.com/snippets/css/a-guide-to-flexbox/", "Panduan visual Flexbox yang banyak dirujuk.", "A widely referenced visual guide to Flexbox.")],
 "javascript": [("MDN: JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "Panduan resmi bahasa JavaScript.", "The official JavaScript language guide."),
                ("javascript.info", "https://javascript.info", "Tutorial modern dari dasar sampai topik lanjut.", "A modern tutorial from the basics to advanced topics."),
                ("freeCodeCamp", "https://www.freecodecamp.org/learn", "Latihan JavaScript dan proyek gratis.", "Free JavaScript exercises and projects.")],
 "python": [("Python Tutorial (docs.python.org)", "https://docs.python.org/3/tutorial/", "Tutorial resmi Python.", "The official Python tutorial."),
            ("Python Getting Started", "https://www.python.org/about/gettingstarted/", "Panduan memulai dari python.org.", "A getting-started guide from python.org."),
            ("Real Python", "https://realpython.com", "Artikel dan tutorial Python mendalam.", "In-depth Python articles and tutorials.")],
 "sql": [("SQLBolt", "https://sqlbolt.com", "Pelajaran SQL interaktif langkah demi langkah.", "Interactive step-by-step SQL lessons."),
         ("PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html", "Tutorial resmi untuk memahami SQL dan basis data.", "The official tutorial for understanding SQL and databases."),
         ("SQLite SQL Reference", "https://www.sqlite.org/lang.html", "Referensi sintaks SQL yang ringkas.", "A concise SQL syntax reference.")],
 "java": [("Oracle Java Tutorials", "https://docs.oracle.com/javase/tutorial/", "Tutorial resmi Java dari Oracle.", "The official Java tutorials from Oracle."),
          ("dev.java Learn", "https://dev.java/learn/", "Jalur belajar Java modern.", "A modern Java learning path."),
          ("Java API Documentation", "https://docs.oracle.com/en/java/javase/21/docs/api/", "Dokumentasi pustaka standar Java.", "Documentation for the Java standard library.")],
 "php": [("PHP Manual", "https://www.php.net/manual/en/", "Manual resmi PHP.", "The official PHP manual."),
         ("PHP: The Right Way", "https://phptherightway.com", "Praktik terbaik PHP modern.", "Modern PHP best practices."),
         ("PHP Getting Started", "https://www.php.net/manual/en/getting-started.php", "Memulai PHP langkah demi langkah.", "Getting started with PHP step by step.")],
 "c": [("cppreference: C", "https://en.cppreference.com/w/c", "Referensi bahasa C dan pustaka standarnya.", "A reference for the C language and its standard library."),
       ("Beej's Guide to C", "https://beej.us/guide/bgc/", "Panduan C yang mudah dibaca.", "An approachable guide to C."),
       ("GNU C Library Manual", "https://www.gnu.org/software/libc/manual/", "Manual pustaka C GNU.", "The GNU C Library manual.")],
 "cpp": [("cppreference: C++", "https://en.cppreference.com/w/cpp", "Referensi C++ dan STL.", "A reference for C++ and the STL."),
         ("learncpp.com", "https://www.learncpp.com", "Tutorial C++ gratis yang sangat lengkap.", "A very thorough free C++ tutorial."),
         ("Standard C++ FAQ", "https://isocpp.org/wiki/faq", "Tanya jawab resmi dari komunitas C++.", "The official C++ community FAQ.")],
 "csharp": [("Microsoft Learn: C#", "https://learn.microsoft.com/en-us/dotnet/csharp/", "Dokumentasi dan panduan C# resmi.", "Official C# documentation and guides."),
            ("A Tour of C#", "https://learn.microsoft.com/en-us/dotnet/csharp/tour-of-csharp/", "Pengenalan fitur utama C#.", "An introduction to the main C# features."),
            (".NET Documentation", "https://learn.microsoft.com/en-us/dotnet/", "Dokumentasi platform .NET.", "Documentation for the .NET platform.")],
 "react": [("react.dev: Learn", "https://react.dev/learn", "Tutorial resmi React.", "The official React tutorial."),
           ("React Reference", "https://react.dev/reference/react", "Referensi API React termasuk hook.", "React API reference including hooks."),
           ("Thinking in React", "https://react.dev/learn/thinking-in-react", "Cara berpikir membangun UI dengan React.", "How to think when building UIs with React.")],
 "mysql": [("MySQL Tutorial", "https://dev.mysql.com/doc/refman/8.0/en/tutorial.html", "Tutorial resmi MySQL.", "The official MySQL tutorial."),
           ("MySQL Data Types", "https://dev.mysql.com/doc/refman/8.0/en/data-types.html", "Daftar tipe data MySQL.", "The list of MySQL data types."),
           ("MySQL EXPLAIN", "https://dev.mysql.com/doc/refman/8.0/en/explain.html", "Membaca rencana eksekusi query.", "Reading a query's execution plan.")],
}
