SENTENCE_BANK = {
    "A1": [
        {
            "prompt_en": "I go jogging every morning.",
            "target_de": "Ich gehe jeden Morgen joggen.",
            "tokens": ["Ich", "gehe", "jeden", "Morgen", "joggen", "."],
            "distractors": ["oft", "im", "Park", "später"],
            "hint_en": "Verb in 2nd position; time can follow subject.",
            "grammar_tag": "Verb-2; TMP",
            "weight": 1
        },
        {
            "prompt_en": "Do you have siblings?",
            "target_de": "Hast du Geschwister?",
            "tokens": ["Hast", "du", "Geschwister", "?"],
            "distractors": ["die", "hast", "ist", "Wo"],
            "hint_en": "Yes/No question: verb first.",
            "grammar_tag": "Ja/Nein-Frage",
            "weight": 1
        },
        {
            "prompt_en": "We are going to the supermarket today.",
            "target_de": "Wir gehen heute zum Supermarkt.",
            "tokens": ["Wir", "gehen", "heute", "zum", "Supermarkt", "."],
            "distractors": ["ins", "gehen", "morgen"],
            "hint_en": "Verb 2nd, time after subject, place after time.",
            "grammar_tag": "TMP",
            "weight": 1
        },
        {
            "prompt_en": "My name is Anna.",
            "target_de": "Ich heiße Anna.",
            "tokens": ["Ich", "heiße", "Anna", "."],
            "distractors": ["bin", "Name", "habe"],
            "hint_en": "Introduce yourself with ‘heißen’.",
            "grammar_tag": "Vorstellung",
            "weight": 1
        },
        {
            "prompt_en": "We live in Berlin.",
            "target_de": "Wir wohnen in Berlin.",
            "tokens": ["Wir", "wohnen", "in", "Berlin", "."],
            "distractors": ["nach", "wohne", "im"],
            "hint_en": "‘wohnen’ + in + city.",
            "grammar_tag": "Präpositionen",
            "weight": 1
        },
        {
            "prompt_en": "I would like a coffee, please.",
            "target_de": "Ich möchte einen Kaffee, bitte.",
            "tokens": ["Ich", "möchte", "einen", "Kaffee", ",", "bitte", "."],
            "distractors": ["haben", "die", "mochte"],
            "hint_en": "möchte + Akkusativ.",
            "grammar_tag": "Bestellung",
            "weight": 1
        },
        {
            "prompt_en": "The bus arrives at 8 o'clock.",
            "target_de": "Der Bus kommt um acht Uhr an.",
            "tokens": ["Der", "Bus", "kommt", "um", "acht", "Uhr", "an", "."],
            "distractors": ["an", "fahren", "achtzehn"],
            "hint_en": "Separable verb ‘ankommen’.",
            "grammar_tag": "Trennbare Verben",
            "weight": 1
        },
        {
            "prompt_en": "Where is the toilet?",
            "target_de": "Wo ist die Toilette?",
            "tokens": ["Wo", "ist", "die", "Toilette", "?"],
            "distractors": ["wann", "wer", "woher"],
            "hint_en": "W-Question: verb in 2nd position.",
            "grammar_tag": "Fragen",
            "weight": 1
        },
        {
            "prompt_en": "I am learning German.",
            "target_de": "Ich lerne Deutsch.",
            "tokens": ["Ich", "lerne", "Deutsch", "."],
            "distractors": ["lernen", "lernst", "sprichst"],
            "hint_en": "Simple present tense, verb 2nd.",
            "grammar_tag": "Präsens",
            "weight": 1
        },
        {
            "prompt_en": "She works in a school.",
            "target_de": "Sie arbeitet in einer Schule.",
            "tokens": ["Sie", "arbeitet", "in", "einer", "Schule", "."],
            "distractors": ["im", "arbeiten", "ein"],
            "hint_en": "in + Dativ for location.",
            "grammar_tag": "Präpositionen + Dativ",
            "weight": 1
        },
        {
            "prompt_en": "What is your phone number?",
            "target_de": "Wie ist deine Telefonnummer?",
            "tokens": ["Wie", "ist", "deine", "Telefonnummer", "?"],
            "distractors": ["Wo", "Wann", "Wer"],
            "hint_en": "Use ‘Wie ist…?’ to ask for numbers.",
            "grammar_tag": "Fragen",
            "weight": 1
        },
        {
            "prompt_en": "I like pizza.",
            "target_de": "Ich mag Pizza.",
            "tokens": ["Ich", "mag", "Pizza", "."],
            "distractors": ["möchte", "liebe", "esse"],
            "hint_en": "Use ‘mögen’ to talk about likes.",
            "grammar_tag": "Modalverb mögen",
            "weight": 1
        },
        {
            "prompt_en": "Can you repeat that, please?",
            "target_de": "Kannst du das bitte wiederholen?",
            "tokens": ["Kannst", "du", "das", "bitte", "wiederholen", "?"],
            "distractors": ["kannst", "wiederhole", "du"],
            "hint_en": "Yes/No question: modal verb first.",
            "grammar_tag": "Modalverben; Frage",
            "weight": 1
        },
        {
            "prompt_en": "The bakery is next to the bank.",
            "target_de": "Die Bäckerei ist neben der Bank.",
            "tokens": ["Die", "Bäckerei", "ist", "neben", "der", "Bank", "."],
            "distractors": ["neben", "dem", "Bank"],
            "hint_en": "neben + Dativ (location).",
            "grammar_tag": "Wechselpräposition (Dativ)",
            "weight": 1
        },
        {
            "prompt_en": "I don’t understand.",
            "target_de": "Ich verstehe nicht.",
            "tokens": ["Ich", "verstehe", "nicht", "."],
            "distractors": ["kein", "keine", "nichts"],
            "hint_en": "Use ‘nicht’ to negate the verb.",
            "grammar_tag": "Negation",
            "weight": 1
        },
        {
            "prompt_en": "At what time does the class start?",
            "target_de": "Um wie viel Uhr beginnt der Kurs?",
            "tokens": ["Um", "wie", "viel", "Uhr", "beginnt", "der", "Kurs", "?"],
            "distractors": ["Wann", "beginnen", "Kurs"],
            "hint_en": "Asking for time with ‘Um wie viel Uhr…’.",
            "grammar_tag": "Fragen; Zeit",
            "weight": 1
        },
        {
            "prompt_en": "I’m sorry, I’m late.",
            "target_de": "Entschuldigung, ich bin spät.",
            "tokens": ["Entschuldigung", ",", "ich", "bin", "spät", "."],
            "distractors": ["später", "habe", "ist"],
            "hint_en": "Fixed apology phrase.",
            "grammar_tag": "Redemittel",
            "weight": 1
        },
        {
            "prompt_en": "We need two tickets.",
            "target_de": "Wir brauchen zwei Tickets.",
            "tokens": ["Wir", "brauchen", "zwei", "Tickets", "."],
            "distractors": ["brauche", "Ticket", "zweite"],
            "hint_en": "Plural nouns without article in general count.",
            "grammar_tag": "Akkusativ; Plural",
            "weight": 1
        },
        {
            "prompt_en": "He is from Spain.",
            "target_de": "Er kommt aus Spanien.",
            "tokens": ["Er", "kommt", "aus", "Spanien", "."],
            "distractors": ["von", "Spanischem", "Spanier"],
            "hint_en": "aus + Land for origin.",
            "grammar_tag": "Präpositionen",
            "weight": 1
        },
        {
            "prompt_en": "The window is open.",
            "target_de": "Das Fenster ist offen.",
            "tokens": ["Das", "Fenster", "ist", "offen", "."],
            "distractors": ["auf", "öffnen", "macht"],
            "hint_en": "Simple statement with ‘sein’.",
            "grammar_tag": "Präsens sein",
            "weight": 1
        }
    ],

    "A2": [
        {
            "prompt_en": "I am staying at home because I am sick.",
            "target_de": "Ich bleibe heute zu Hause, weil ich krank bin.",
            "tokens": ["Ich", "bleibe", "heute", "zu", "Hause", ",", "weil", "ich", "krank", "bin", "."],
            "distractors": ["deshalb", "werde", "morgen"],
            "hint_en": "‘weil’ sends the verb to the end.",
            "grammar_tag": "weil",
            "weight": 1
        },
        {
            "prompt_en": "Tomorrow I will visit my friend.",
            "target_de": "Morgen besuche ich meinen Freund.",
            "tokens": ["Morgen", "besuche", "ich", "meinen", "Freund", "."],
            "distractors": ["werde", "besuchen", "Freunde"],
            "hint_en": "Time first → inversion (verb before subject).",
            "grammar_tag": "Inversion",
            "weight": 1
        },
        {
            "prompt_en": "She is reading a book and drinking tea.",
            "target_de": "Sie liest ein Buch und trinkt Tee.",
            "tokens": ["Sie", "liest", "ein", "Buch", "und", "trinkt", "Tee", "."],
            "distractors": ["oder", "Bücher", "trinken"],
            "hint_en": "Coordinate clauses with ‘und’.",
            "grammar_tag": "Konjunktionen",
            "weight": 1
        },
        {
            "prompt_en": "He has to go to the doctor.",
            "target_de": "Er muss zum Arzt gehen.",
            "tokens": ["Er", "muss", "zum", "Arzt", "gehen", "."],
            "distractors": ["geht", "gehen", "ins"],
            "hint_en": "Modal verb + infinitive at the end.",
            "grammar_tag": "Modalverben",
            "weight": 1
        },
        {
            "prompt_en": "We are interested in the new film.",
            "target_de": "Wir interessieren uns für den neuen Film.",
            "tokens": ["Wir", "interessieren", "uns", "für", "den", "neuen", "Film", "."],
            "distractors": ["an", "im", "alte"],
            "hint_en": "sich interessieren für + Akkusativ.",
            "grammar_tag": "Reflexiv + Präposition",
            "weight": 1
        },
        {
            "prompt_en": "It’s raining, therefore we’re staying inside.",
            "target_de": "Es regnet, deshalb bleiben wir drinnen.",
            "tokens": ["Es", "regnet", ",", "deshalb", "bleiben", "wir", "drinnen", "."],
            "distractors": ["weil", "obwohl", "damit"],
            "hint_en": "‘deshalb’ = connector; main clause word order.",
            "grammar_tag": "Folge: deshalb",
            "weight": 1
        },
        {
            "prompt_en": "I’m trying to learn more German.",
            "target_de": "Ich versuche, mehr Deutsch zu lernen.",
            "tokens": ["Ich", "versuche", ",", "mehr", "Deutsch", "zu", "lernen", "."],
            "distractors": ["lernen", "zum", "Deutsch"],
            "hint_en": "zu + Infinitiv construction.",
            "grammar_tag": "zu-Infinitiv",
            "weight": 1
        },
        {
            "prompt_en": "When I have time, I cook.",
            "target_de": "Wenn ich Zeit habe, koche ich.",
            "tokens": ["Wenn", "ich", "Zeit", "habe", ",", "koche", "ich", "."],
            "distractors": ["Weil", "Dann", "habe"],
            "hint_en": "Subordinate clause first → inversion in main clause.",
            "grammar_tag": "Temporalsatz wenn",
            "weight": 1
        },
        {
            "prompt_en": "I have already finished my homework.",
            "target_de": "Ich habe meine Hausaufgaben schon fertig gemacht.",
            "tokens": ["Ich", "habe", "meine", "Hausaufgaben", "schon", "fertig", "gemacht", "."],
            "distractors": ["bin", "gemacht", "machen"],
            "hint_en": "Perfekt with ‘haben’.",
            "grammar_tag": "Perfekt",
            "weight": 1
        },
        {
            "prompt_en": "We moved to a bigger apartment.",
            "target_de": "Wir sind in eine größere Wohnung umgezogen.",
            "tokens": ["Wir", "sind", "in", "eine", "größere", "Wohnung", "umgezogen", "."],
            "distractors": ["haben", "umgezogen", "umziehen"],
            "hint_en": "Perfekt with ‘sein’ (movement change).",
            "grammar_tag": "Perfekt mit sein",
            "weight": 1
        },
        {
            "prompt_en": "First we eat, then we go for a walk.",
            "target_de": "Zuerst essen wir, dann gehen wir spazieren.",
            "tokens": ["Zuerst", "essen", "wir", ",", "dann", "gehen", "wir", "spazieren", "."],
            "distractors": ["weil", "obwohl", "spazierengehen"],
            "hint_en": "Sequencing with adverbs; verb 2nd each clause.",
            "grammar_tag": "Satzadverbien",
            "weight": 1
        },
        {
            "prompt_en": "I don’t have any time today.",
            "target_de": "Ich habe heute keine Zeit.",
            "tokens": ["Ich", "habe", "heute", "keine", "Zeit", "."],
            "distractors": ["nicht", "kein", "Zeiten"],
            "hint_en": "Use ‘kein/keine’ to negate nouns.",
            "grammar_tag": "Negation mit kein",
            "weight": 1
        },
        {
            "prompt_en": "We’re looking forward to the weekend.",
            "target_de": "Wir freuen uns auf das Wochenende.",
            "tokens": ["Wir", "freuen", "uns", "auf", "das", "Wochenende", "."],
            "distractors": ["für", "am", "im"],
            "hint_en": "sich freuen auf + Akkusativ.",
            "grammar_tag": "Reflexiv + Präp.",
            "weight": 1
        },
        {
            "prompt_en": "Could you help me, please?",
            "target_de": "Könnten Sie mir bitte helfen?",
            "tokens": ["Könnten", "Sie", "mir", "bitte", "helfen", "?"],
            "distractors": ["Kannst", "hilfst", "Hilfe"],
            "hint_en": "Polite request with Konjunktiv II of ‘können’.",
            "grammar_tag": "Höflichkeit",
            "weight": 1
        },
        {
            "prompt_en": "I have been living here for two years.",
            "target_de": "Ich wohne seit zwei Jahren hier.",
            "tokens": ["Ich", "wohne", "seit", "zwei", "Jahren", "hier", "."],
            "distractors": ["für", "vor", "Jahre"],
            "hint_en": "seit + Dativ for duration up to now.",
            "grammar_tag": "Zeitangabe seit",
            "weight": 1
        },
        {
            "prompt_en": "As soon as I finish work, I call you.",
            "target_de": "Sobald ich mit der Arbeit fertig bin, rufe ich dich an.",
            "tokens": ["Sobald", "ich", "mit", "der", "Arbeit", "fertig", "bin", ",", "rufe", "ich", "dich", "an", "."],
            "distractors": ["weil", "deshalb", "rufen"],
            "hint_en": "Subordinate clause first; separable verb ‘anrufen’.",
            "grammar_tag": "Temporalsatz sobald; trennbar",
            "weight": 1
        },
        {
            "prompt_en": "I don’t know if he is at home.",
            "target_de": "Ich weiß nicht, ob er zu Hause ist.",
            "tokens": ["Ich", "weiß", "nicht", ",", "ob", "er", "zu", "Hause", "ist", "."],
            "distractors": ["dass", "weil", "wann"],
            "hint_en": "Indirect yes/no question with ‘ob’.",
            "grammar_tag": "Nebensatz ob",
            "weight": 1
        },
        {
            "prompt_en": "My sister is taller than me.",
            "target_de": "Meine Schwester ist größer als ich.",
            "tokens": ["Meine", "Schwester", "ist", "größer", "als", "ich", "."],
            "distractors": ["wie", "groß", "am"],
            "hint_en": "Comparative with ‘als’.",
            "grammar_tag": "Komparativ",
            "weight": 1
        },
        {
            "prompt_en": "I need to pick up the package.",
            "target_de": "Ich muss das Paket abholen.",
            "tokens": ["Ich", "muss", "das", "Paket", "abholen", "."],
            "distractors": ["hole", "ab", "abgeholt"],
            "hint_en": "Modal + separable verb (infinitive at the end).",
            "grammar_tag": "Modal + trennbar",
            "weight": 1
        },
        {
            "prompt_en": "He likes playing football the most.",
            "target_de": "Am liebsten spielt er Fußball.",
            "tokens": ["Am", "liebsten", "spielt", "er", "Fußball", "."],
            "distractors": ["Lieblings", "am", "liebe"],
            "hint_en": "Superlative of ‘gern’: gern → lieber → am liebsten.",
            "grammar_tag": "Steigerung gern",
            "weight": 1
        }
    ],

    "B1": [
        {
            "prompt_en": "I know that you are coming tomorrow.",
            "target_de": "Ich weiß, dass du morgen kommst.",
            "tokens": ["Ich", "weiß", ",", "dass", "du", "morgen", "kommst", "."],
            "distractors": ["kommst", "dann", "sein"],
            "hint_en": "‘dass’ clause: verb at the end.",
            "grammar_tag": "dass",
            "weight": 1
        },
        {
            "prompt_en": "Although it was raining, we went out.",
            "target_de": "Obwohl es geregnet hat, sind wir ausgegangen.",
            "tokens": ["Obwohl", "es", "geregnet", "hat", ",", "sind", "wir", "ausgegangen", "."],
            "distractors": ["Weil", "Deshalb", "ob"],
            "hint_en": "Concessive clause with ‘obwohl’; Perfekt.",
            "grammar_tag": "Obwohl; Perfekt",
            "weight": 1
        },
        {
            "prompt_en": "Could you tell me where the station is?",
            "target_de": "Könnten Sie mir sagen, wo der Bahnhof ist?",
            "tokens": ["Könnten", "Sie", "mir", "sagen", ",", "wo", "der", "Bahnhof", "ist", "?"],
            "distractors": ["wann", "wer", "wie"],
            "hint_en": "Indirect question: verb at the end.",
            "grammar_tag": "Indirekte Frage",
            "weight": 1
        },
        {
            "prompt_en": "He said that he would come later.",
            "target_de": "Er hat gesagt, dass er später kommen würde.",
            "tokens": ["Er", "hat", "gesagt", ",", "dass", "er", "später", "kommen", "würde", "."],
            "distractors": ["wird", "kommt", "kam"],
            "hint_en": "Reported speech with ‘würde’.",
            "grammar_tag": "Indirekte Rede (würde)",
            "weight": 1
        },
        {
            "prompt_en": "If I had more time, I would travel more.",
            "target_de": "Wenn ich mehr Zeit hätte, würde ich mehr reisen.",
            "tokens": ["Wenn", "ich", "mehr", "Zeit", "hätte", ",", "würde", "ich", "mehr", "reisen", "."],
            "distractors": ["habe", "werde", "würden"],
            "hint_en": "Irrealis with Konjunktiv II.",
            "grammar_tag": "Konjunktiv II Konditional",
            "weight": 1
        },
        {
            "prompt_en": "The book that I am reading is exciting.",
            "target_de": "Das Buch, das ich lese, ist spannend.",
            "tokens": ["Das", "Buch", ",", "das", "ich", "lese", ",", "ist", "spannend", "."],
            "distractors": ["welche", "was", "dem"],
            "hint_en": "Relative clause with ‘das’.",
            "grammar_tag": "Relativsatz",
            "weight": 1
        },
        {
            "prompt_en": "I’m used to getting up early.",
            "target_de": "Ich bin daran gewöhnt, früh aufzustehen.",
            "tokens": ["Ich", "bin", "daran", "gewöhnt", ",", "früh", "aufzustehen", "."],
            "distractors": ["gewohnt", "aufstehen", "früher"],
            "hint_en": "Adjective + zu-Infinitiv; fixed phrase.",
            "grammar_tag": "zu-Infinitiv; Redemittel",
            "weight": 1
        },
        {
            "prompt_en": "The film was not as good as expected.",
            "target_de": "Der Film war nicht so gut, wie erwartet.",
            "tokens": ["Der", "Film", "war", "nicht", "so", "gut", ",", "wie", "erwartet", "."],
            "distractors": ["als", "besser", "am"],
            "hint_en": "so … wie for comparison of equality.",
            "grammar_tag": "Vergleich so…wie",
            "weight": 1
        },
        {
            "prompt_en": "While he was cooking, I set the table.",
            "target_de": "Während er kochte, deckte ich den Tisch.",
            "tokens": ["Während", "er", "kochte", ",", "deckte", "ich", "den", "Tisch", "."],
            "distractors": ["Wenn", "Als", "Nachdem"],
            "hint_en": "Temporal clause with ‘während’ (Präteritum).",
            "grammar_tag": "Temporalsatz während",
            "weight": 1
        },
        {
            "prompt_en": "After we arrived, we called our parents.",
            "target_de": "Nachdem wir angekommen waren, haben wir unsere Eltern angerufen.",
            "tokens": ["Nachdem", "wir", "angekommen", "waren", ",", "haben", "wir", "unsere", "Eltern", "angerufen", "."],
            "distractors": ["Nachdem", "ist", "rufen"],
            "hint_en": "Plusquamperfekt in the subordinate clause.",
            "grammar_tag": "Nachdem; Plusquamperfekt",
            "weight": 1
        },
        {
            "prompt_en": "You should do more sport.",
            "target_de": "Du solltest mehr Sport machen.",
            "tokens": ["Du", "solltest", "mehr", "Sport", "machen", "."],
            "distractors": ["sollst", "Sporten", "machst"],
            "hint_en": "Advice with Konjunktiv II of ‘sollen’.",
            "grammar_tag": "Ratschlag",
            "weight": 1
        },
        {
            "prompt_en": "The meeting was postponed because the boss was ill.",
            "target_de": "Die Besprechung wurde verschoben, weil der Chef krank war.",
            "tokens": ["Die", "Besprechung", "wurde", "verschoben", ",", "weil", "der", "Chef", "krank", "war", "."],
            "distractors": ["ist", "hat", "verschob"],
            "hint_en": "Passive in Präteritum + ‘weil’.",
            "grammar_tag": "Passiv Präteritum; weil",
            "weight": 1
        },
        {
            "prompt_en": "I’m looking for a job that offers flexibility.",
            "target_de": "Ich suche eine Stelle, die Flexibilität bietet.",
            "tokens": ["Ich", "suche", "eine", "Stelle", ",", "die", "Flexibilität", "bietet", "."],
            "distractors": ["welche", "bieten", "anbietet"],
            "hint_en": "Relative clause with ‘die’.",
            "grammar_tag": "Relativsatz",
            "weight": 1
        },
        {
            "prompt_en": "It depends on the weather.",
            "target_de": "Es hängt vom Wetter ab.",
            "tokens": ["Es", "hängt", "vom", "Wetter", "ab", "."],
            "distractors": ["von", "Wetter", "ist"],
            "hint_en": "Verb-preposition phrase with separable verb.",
            "grammar_tag": "Verb + Präp.; trennbar",
            "weight": 1
        },
        {
            "prompt_en": "As far as I know, the store is closed.",
            "target_de": "Soweit ich weiß, ist das Geschäft geschlossen.",
            "tokens": ["Soweit", "ich", "weiß", ",", "ist", "das", "Geschäft", "geschlossen", "."],
            "distractors": ["Sofern", "Soviel", "war"],
            "hint_en": "Fixed phrase ‘Soweit ich weiß’.",
            "grammar_tag": "Redemittel",
            "weight": 1
        },
        {
            "prompt_en": "He apologized for the mistake.",
            "target_de": "Er hat sich für den Fehler entschuldigt.",
            "tokens": ["Er", "hat", "sich", "für", "den", "Fehler", "entschuldigt", "."],
            "distractors": ["entschuldigte", "entschuldigen", "bei"],
            "hint_en": "sich entschuldigen für + Akk.",
            "grammar_tag": "Reflexiv + Präp.",
            "weight": 1
        },
        {
            "prompt_en": "If the train is late, we will take a taxi.",
            "target_de": "Falls der Zug verspätet ist, nehmen wir ein Taxi.",
            "tokens": ["Falls", "der", "Zug", "verspätet", "ist", ",", "nehmen", "wir", "ein", "Taxi", "."],
            "distractors": ["Wenn", "würden", "nahm"],
            "hint_en": "Conditional with ‘falls’.",
            "grammar_tag": "Konditionalsatz",
            "weight": 1
        },
        {
            "prompt_en": "I ended up buying the cheaper one.",
            "target_de": "Am Ende habe ich das günstigere gekauft.",
            "tokens": ["Am", "Ende", "habe", "ich", "das", "günstigere", "gekauft", "."],
            "distractors": ["Endlich", "gekauft", "kaufe"],
            "hint_en": "Idiomatic time adverb + Perfekt.",
            "grammar_tag": "Zeitangabe; Perfekt",
            "weight": 1
        },
        {
            "prompt_en": "The more I practice, the better I get.",
            "target_de": "Je mehr ich übe, desto besser werde ich.",
            "tokens": ["Je", "mehr", "ich", "übe", ",", "desto", "besser", "werde", "ich", "."],
            "distractors": ["umso", "je", "bester"],
            "hint_en": "Comparative correlative ‘je … desto’.",
            "grammar_tag": "Je…desto",
            "weight": 1
        },
        {
            "prompt_en": "I didn’t expect that.",
            "target_de": "Damit habe ich nicht gerechnet.",
            "tokens": ["Damit", "habe", "ich", "nicht", "gerechnet", "."],
            "distractors": ["Dafür", "Darauf", "rechnete"],
            "hint_en": "Fixed verb-preposition phrase.",
            "grammar_tag": "Redemittel; Verb + Präp.",
            "weight": 1
        }
    ],

    "B2": [
        {
            "prompt_en": "The car that I bought is red.",
            "target_de": "Das Auto, das ich gekauft habe, ist rot.",
            "tokens": ["Das", "Auto", ",", "das", "ich", "gekauft", "habe", ",", "ist", "rot", "."],
            "distractors": ["welche", "hatte", "mehr"],
            "hint_en": "Relative clause: verb at the end of the clause.",
            "grammar_tag": "Relativsatz",
            "weight": 1
        },
        {
            "prompt_en": "It is assumed that prices will rise.",
            "target_de": "Es wird angenommen, dass die Preise steigen werden.",
            "tokens": ["Es", "wird", "angenommen", ",", "dass", "die", "Preise", "steigen", "werden", "."],
            "distractors": ["steigen", "gestiegen", "wurden"],
            "hint_en": "Impersonal passive + ‘dass’.",
            "grammar_tag": "Passiv unpersönlich",
            "weight": 1
        },
        {
            "prompt_en": "Despite the rain, the concert took place.",
            "target_de": "Trotz des Regens hat das Konzert stattgefunden.",
            "tokens": ["Trotz", "des", "Regens", "hat", "das", "Konzert", "stattgefunden", "."],
            "distractors": ["Obwohl", "wegen", "stattfindet"],
            "hint_en": "Genitive with ‘trotz’.",
            "grammar_tag": "Präp. mit Genitiv",
            "weight": 1
        },
        {
            "prompt_en": "He explained the problem in a way that everyone understood it.",
            "target_de": "Er erklärte das Problem so, dass es alle verstanden.",
            "tokens": ["Er", "erklärte", "das", "Problem", "so", ",", "dass", "es", "alle", "verstanden", "."],
            "distractors": ["damit", "weil", "obwohl"],
            "hint_en": "Consecutive clause ‘so … dass’.",
            "grammar_tag": "Konsekutivsatz",
            "weight": 1
        },
        {
            "prompt_en": "If I had known that earlier, I would have reacted differently.",
            "target_de": "Hätte ich das früher gewusst, hätte ich anders reagiert.",
            "tokens": ["Hätte", "ich", "das", "früher", "gewusst", ",", "hätte", "ich", "anders", "reagiert", "."],
            "distractors": ["Wenn", "würde", "gewollt"],
            "hint_en": "Inversion with omitted ‘wenn’; Konjunktiv II Vergangenheit.",
            "grammar_tag": "Konditionalsatz; Konjunktiv II",
            "weight": 1
        },
        {
            "prompt_en": "The project was completed within the agreed time frame.",
            "target_de": "Das Projekt wurde innerhalb des vereinbarten Zeitrahmens abgeschlossen.",
            "tokens": ["Das", "Projekt", "wurde", "innerhalb", "des", "vereinbarten", "Zeitrahmens", "abgeschlossen", "."],
            "distractors": ["im", "zwischen", "Zeit"],
            "hint_en": "Nominal style + Genitive after preposition.",
            "grammar_tag": "Nominalstil; Genitiv",
            "weight": 1
        },
        {
            "prompt_en": "The article deals with the topic of climate change.",
            "target_de": "Der Artikel setzt sich mit dem Thema Klimawandel auseinander.",
            "tokens": ["Der", "Artikel", "setzt", "sich", "mit", "dem", "Thema", "Klimawandel", "auseinander", "."],
            "distractors": ["über", "an", "darüber"],
            "hint_en": "Fixed reflexive verb + Präposition.",
            "grammar_tag": "Verb + Präp.",
            "weight": 1
        },
        {
            "prompt_en": "He denied having made a mistake.",
            "target_de": "Er bestritt, einen Fehler gemacht zu haben.",
            "tokens": ["Er", "bestritt", ",", "einen", "Fehler", "gemacht", "zu", "haben", "."],
            "distractors": ["dass", "zu", "machen"],
            "hint_en": "zu-Infinitiv (Perfekt) after certain verbs.",
            "grammar_tag": "zu-Infinitiv Perfekt",
            "weight": 1
        },
        {
            "prompt_en": "The results, which were published yesterday, are surprising.",
            "target_de": "Die Ergebnisse, die gestern veröffentlicht wurden, sind überraschend.",
            "tokens": ["Die", "Ergebnisse", ",", "die", "gestern", "veröffentlicht", "wurden", ",", "sind", "überraschend", "."],
            "distractors": ["welche", "worden", "waren"],
            "hint_en": "Relative clause + passive.",
            "grammar_tag": "Relativsatz; Passiv",
            "weight": 1
        },
        {
            "prompt_en": "In contrast to last year, sales have increased.",
            "target_de": "Im Gegensatz zum letzten Jahr sind die Umsätze gestiegen.",
            "tokens": ["Im", "Gegensatz", "zum", "letzten", "Jahr", "sind", "die", "Umsätze", "gestiegen", "."],
            "distractors": ["Gegenteil", "zum", "wurden"],
            "hint_en": "Fixed prepositional phrase.",
            "grammar_tag": "Feste Wendung",
            "weight": 1
        },
        {
            "prompt_en": "It is questionable whether the plan will work.",
            "target_de": "Es ist fraglich, ob der Plan funktionieren wird.",
            "tokens": ["Es", "ist", "fraglich", ",", "ob", "der", "Plan", "funktionieren", "wird", "."],
            "distractors": ["dass", "wenn", "würde"],
            "hint_en": "‘ob’ clause expressing doubt.",
            "grammar_tag": "Indirekte Frage ob",
            "weight": 1
        },
        {
            "prompt_en": "The more complex the task, the more time we need.",
            "target_de": "Je komplexer die Aufgabe ist, desto mehr Zeit brauchen wir.",
            "tokens": ["Je", "komplexer", "die", "Aufgabe", "ist", ",", "desto", "mehr", "Zeit", "brauchen", "wir", "."],
            "distractors": ["umso", "je", "braucht"],
            "hint_en": "‘je … desto’ with adjective in comparative.",
            "grammar_tag": "Je…desto",
            "weight": 1
        },
        {
            "prompt_en": "Contrary to expectations, the meeting was short.",
            "target_de": "Entgegen den Erwartungen war die Besprechung kurz.",
            "tokens": ["Entgegen", "den", "Erwartungen", "war", "die", "Besprechung", "kurz", "."],
            "distractors": ["Gegen", "Entgegen", "Erwartung"],
            "hint_en": "Preposition ‘entgegen’ takes Dative (plural).",
            "grammar_tag": "Präp. Dativ",
            "weight": 1
        },
        {
            "prompt_en": "He acted as if nothing had happened.",
            "target_de": "Er verhielt sich, als ob nichts passiert wäre.",
            "tokens": ["Er", "verhielt", "sich", ",", "als", "ob", "nichts", "passiert", "wäre", "."],
            "distractors": ["war", "sei", "würde"],
            "hint_en": "‘als ob’ + Konjunktiv II (past).",
            "grammar_tag": "Vergleichssatz als ob",
            "weight": 1
        },
        {
            "prompt_en": "It was not until yesterday that I received the email.",
            "target_de": "Erst gestern habe ich die E-Mail bekommen.",
            "tokens": ["Erst", "gestern", "habe", "ich", "die", "E-Mail", "bekommen", "."],
            "distractors": ["Nur", "erst", "bekam"],
            "hint_en": "Focus with ‘erst’ + inversion.",
            "grammar_tag": "Fokus; Inversion",
            "weight": 1
        },
        {
            "prompt_en": "Given the circumstances, the decision is understandable.",
            "target_de": "Angesichts der Umstände ist die Entscheidung nachvollziehbar.",
            "tokens": ["Angesichts", " der", " Umstände", " ist", " die", " Entscheidung", " nachvollziehbar", "."],
            "distractors": ["Wegen", "Trotz", "Angesicht"],
            "hint_en": "Genitive preposition ‘angesichts’.",
            "grammar_tag": "Präp. Genitiv",
            "weight": 1
        },
        {
            "prompt_en": "He is considered a reliable employee.",
            "target_de": "Er gilt als zuverlässiger Mitarbeiter.",
            "tokens": ["Er", "gilt", "als", "zuverlässiger", "Mitarbeiter", "."],
            "distractors": ["giltet", "wie", "zuverlässig"],
            "hint_en": "Verb ‘gelten als’.",
            "grammar_tag": "Verb + als",
            "weight": 1
        },
        {
            "prompt_en": "We must ensure that all data is protected.",
            "target_de": "Wir müssen sicherstellen, dass alle Daten geschützt sind.",
            "tokens": ["Wir", "müssen", "sicherstellen", ",", "dass", "alle", "Daten", "geschützt", "sind", "."],
            "distractors": ["werden", "wurden", "schützen"],
            "hint_en": "Verb + ‘dass’-Satz.",
            "grammar_tag": "dass-Satz",
            "weight": 1
        },
        {
            "prompt_en": "Instead of complaining, we should look for solutions.",
            "target_de": "Anstatt zu jammern, sollten wir nach Lösungen suchen.",
            "tokens": ["Anstatt", "zu", "jammern", ",", "sollten", "wir", "nach", "Lösungen", "suchen", "."],
            "distractors": ["stattdessen", "für", "sucht"],
            "hint_en": "‘anstatt zu’ + Infinitiv.",
            "grammar_tag": "Infinitivgruppe",
            "weight": 1
        }
    ],

    "C1": [
        {
            "prompt_en": "Had he prepared better, the outcome would have been different.",
            "target_de": "Hätte er sich besser vorbereitet, wäre das Ergebnis anders ausgefallen.",
            "tokens": ["Hätte", "er", "sich", "besser", "vorbereitet", ",", "wäre", "das", "Ergebnis", "anders", "ausgefallen", "."],
            "distractors": ["Wenn", "hatte", "würde"],
            "hint_en": "Omitted ‘wenn’; Konjunktiv II Vergangenheit.",
            "grammar_tag": "Irrealis; Konjunktiv II",
            "weight": 1
        },
        {
            "prompt_en": "The measures, some of which are controversial, were approved.",
            "target_de": "Die Maßnahmen, von denen einige umstritten sind, wurden verabschiedet.",
            "tokens": ["Die", "Maßnahmen", ",", "von", "denen", "einige", "umstritten", "sind", ",", "wurden", "verabschiedet", "."],
            "distractors": ["die", "welche", "worden"],
            "hint_en": "Prepositional relative clause.",
            "grammar_tag": "Relativsatz mit Präp.",
            "weight": 1
        },
        {
            "prompt_en": "Considering the latest findings, a reassessment seems necessary.",
            "target_de": "In Anbetracht der neuesten Erkenntnisse erscheint eine Neubewertung notwendig.",
            "tokens": ["In", "Anbetracht", "der", "neuesten", "Erkenntnisse", "erscheint", "eine", "Neubewertung", "notwendig", "."],
            "distractors": ["Aufgrund", "Anbetracht", "scheint"],
            "hint_en": "Genitive prepositional phrase; formal register.",
            "grammar_tag": "Nominalstil; Genitiv",
            "weight": 1
        },
        {
            "prompt_en": "It is to be feared that the situation will escalate.",
            "target_de": "Es ist zu befürchten, dass sich die Lage zuspitzen wird.",
            "tokens": ["Es", "ist", "zu", "befürchten", ",", "dass", "sich", "die", "Lage", "zuspitzen", "wird", "."],
            "distractors": ["befürchtet", "zu", "zuspitzt"],
            "hint_en": "zu-Infinitiv + ‘dass’.",
            "grammar_tag": "zu-Infinitiv; dass",
            "weight": 1
        },
        {
            "prompt_en": "Contrary to what was assumed, the figures are inaccurate.",
            "target_de": "Entgegen der Annahme erweisen sich die Zahlen als ungenau.",
            "tokens": ["Entgegen", "der", "Annahme", "erweisen", "sich", "die", "Zahlen", "als", "ungenau", "."],
            "distractors": ["Gegen", "Annähme", "ungenaue"],
            "hint_en": "‘sich erweisen als’ + Prädikativ.",
            "grammar_tag": "Verb + als",
            "weight": 1
        },
        {
            "prompt_en": "Only by investing more can we maintain our competitiveness.",
            "target_de": "Nur durch höhere Investitionen können wir unsere Wettbewerbsfähigkeit erhalten.",
            "tokens": ["Nur", "durch", "höhere", "Investitionen", "können", "wir", "unsere", "Wettbewerbsfähigkeit", "erhalten", "."],
            "distractors": ["könnten", "erhält", "bei"],
            "hint_en": "Fronted adverbial → inversion.",
            "grammar_tag": "Inversion; Fokus",
            "weight": 1
        },
        {
            "prompt_en": "He failed to recognize the risks associated with the plan.",
            "target_de": "Er versäumte, die mit dem Plan verbundenen Risiken zu erkennen.",
            "tokens": ["Er", "versäumte", ",", "die", "mit", "dem", "Plan", "verbundenen", "Risiken", "zu", "erkennen", "."],
            "distractors": ["verbundene", "Risiko", "erkennt"],
            "hint_en": "Participle attribute + zu-Infinitiv.",
            "grammar_tag": "Partizipialattribut",
            "weight": 1
        },
        {
            "prompt_en": "As was to be expected, the negotiations dragged on.",
            "target_de": "Wie zu erwarten war, zogen sich die Verhandlungen in die Länge.",
            "tokens": ["Wie", "zu", "erwarten", "war", ",", "zogen", "sich", "die", "Verhandlungen", "in", "die", "Länge", "."],
            "distractors": ["Wie", "erwartet", "wurden"],
            "hint_en": "Fixed impersonal construction.",
            "grammar_tag": "Feste Wendung",
            "weight": 1
        },
        {
            "prompt_en": "Even if the proposal is revised, fundamental issues remain.",
            "target_de": "Selbst wenn der Vorschlag überarbeitet wird, bleiben grundlegende Probleme bestehen.",
            "tokens": ["Selbst", "wenn", "der", "Vorschlag", "überarbeitet", "wird", ",", "bleiben", "grundlegende", "Probleme", "bestehen", "."],
            "distractors": ["obwohl", "wären", "bleibt"],
            "hint_en": "Concessive conditional ‘selbst wenn’.",
            "grammar_tag": "Konzessivsatz",
            "weight": 1
        },
        {
            "prompt_en": "What is crucial is not the speed but the accuracy.",
            "target_de": "Entscheidend ist nicht die Geschwindigkeit, sondern die Genauigkeit.",
            "tokens": ["Entscheidend", "ist", "nicht", "die", "Geschwindigkeit", ",", "sondern", "die", "Genauigkeit", "."],
            "distractors": ["aber", "doch", "genau"],
            "hint_en": "Cleft-like emphasis; ‘sondern’ after negation.",
            "grammar_tag": "Fokus; sondern",
            "weight": 1
        },
        {
            "prompt_en": "He is said to have influenced the decision.",
            "target_de": "Er soll die Entscheidung beeinflusst haben.",
            "tokens": ["Er", "soll", "die", "Entscheidung", "beeinflusst", "haben", "."],
            "distractors": ["sollte", "hat", "wurde"],
            "hint_en": "Modalverb ‘sollen’ for report/rumor.",
            "grammar_tag": "Indirektheit",
            "weight": 1
        },
        {
            "prompt_en": "The more attention is paid to details, the fewer errors occur.",
            "target_de": "Je mehr auf Details geachtet wird, desto weniger Fehler treten auf.",
            "tokens": ["Je", "mehr", "auf", "Details", "geachtet", "wird", ",", "desto", "weniger", "Fehler", "treten", "auf", "."],
            "distractors": ["je", "weniger", "tritt"],
            "hint_en": "Impersonal passive + je/desto.",
            "grammar_tag": "Passiv; Je…desto",
            "weight": 1
        },
        {
            "prompt_en": "This is a development whose consequences are still unforeseeable.",
            "target_de": "Dies ist eine Entwicklung, deren Folgen noch unabsehbar sind.",
            "tokens": ["Dies", "ist", "eine", "Entwicklung", ",", "deren", "Folgen", "noch", "unabsehbar", "sind", "."],
            "distractors": ["deren", "welcher", "denen"],
            "hint_en": "Genitive relative pronoun ‘deren’.",
            "grammar_tag": "Relativpronomen Genitiv",
            "weight": 1
        },
        {
            "prompt_en": "Not only did the team miss the deadline, but costs also exploded.",
            "target_de": "Nicht nur verpasste das Team die Frist, sondern auch die Kosten explodierten.",
            "tokens": ["Nicht", "nur", "verpasste", "das", "Team", "die", "Frist", ",", "sondern", "auch", "die", "Kosten", "explodierten", "."],
            "distractors": ["aber", "sondern", "explodiert"],
            "hint_en": "‘Nicht nur … sondern auch’ with inversion.",
            "grammar_tag": "Korrelative Konjunktion",
            "weight": 1
        },
        {
            "prompt_en": "There is reason to assume that demand will decrease.",
            "target_de": "Es gibt Anlass zu der Annahme, dass die Nachfrage zurückgehen wird.",
            "tokens": ["Es", "gibt", "Anlass", "zu", "der", "Annahme", ",", "dass", "die", "Nachfrage", "zurückgehen", "wird", "."],
            "distractors": ["zum", "gehen", "würde"],
            "hint_en": "Nominal phrase + ‘dass’.",
            "grammar_tag": "Nominalstil",
            "weight": 1
        },
        {
            "prompt_en": "Far from being perfect, the plan nevertheless offers a basis for discussion.",
            "target_de": "Weit davon entfernt, perfekt zu sein, bietet der Plan dennoch eine Diskussionsgrundlage.",
            "tokens": ["Weit", "davon", "entfernt", ",", "perfekt", "zu", "sein", ",", "bietet", "der", "Plan", "dennoch", "eine", "Diskussionsgrundlage", "."],
            "distractors": ["obwohl", "perfekt", "ist"],
            "hint_en": "Participial preface + main clause.",
            "grammar_tag": "Partizipialkonstruktion",
            "weight": 1
        },
        {
            "prompt_en": "Whether the project will be funded remains to be seen.",
            "target_de": "Ob das Projekt finanziert wird, bleibt abzuwarten.",
            "tokens": ["Ob", "das", "Projekt", "finanziert", "wird", ",", "bleibt", "abzuwarten", "."],
            "distractors": ["dass", "zu", "abwarten"],
            "hint_en": "Impersonal construction with ‘bleibt abzuwarten’.",
            "grammar_tag": "Unpersönliche Form",
            "weight": 1
        },
        {
            "prompt_en": "It is precisely here that the difficulties arise.",
            "target_de": "Gerade hier ergeben sich die Schwierigkeiten.",
            "tokens": ["Gerade", "hier", "ergeben", "sich", "die", "Schwierigkeiten", "."],
            "distractors": ["ergeben", "gibt", "sich"],
            "hint_en": "Focus adverb ‘gerade’.",
            "grammar_tag": "Fokus",
            "weight": 1
        },
        {
            "prompt_en": "No sooner had we started than problems emerged.",
            "target_de": "Kaum hatten wir begonnen, traten schon Probleme auf.",
            "tokens": ["Kaum", "hatten", "wir", "begonnen", ",", "traten", "schon", "Probleme", "auf", "."],
            "distractors": ["Kaum", "beginnen", "aufgetreten"],
            "hint_en": "‘Kaum …, da/als’ pattern; here without ‘da’.",
            "grammar_tag": "Temporale Inversion",
            "weight": 1
        },
        {
            "prompt_en": "It remains unclear to what extent the rule applies.",
            "target_de": "Unklar bleibt, inwiefern die Regel gilt.",
            "tokens": ["Unklar", "bleibt", ",", "inwiefern", "die", "Regel", "gilt", "."],
            "distractors": ["wiefern", "obwohl", "giltet"],
            "hint_en": "Fronted predicate + indirect question.",
            "grammar_tag": "Inversion; Indirekte Frage",
            "weight": 1
        }
    ]
}
