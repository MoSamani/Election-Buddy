# demo_papers.py
# -*- coding: utf-8 -*-

from typing import List, Dict, Any

DEMO_PAPERS: List[Dict[str, Any]] = [
    {
        "external_id": "doi:10.1126/science.abc1234",
        "title": "Climate Change Accelerates Extreme Weather Patterns Worldwide",
        "text": (
            "In dieser Studie analysierten Forscherinnen und Forscher über 40 Jahre Klimadaten. "
            "Die Ergebnisse zeigen eine signifikante Zunahme extremer Wetterereignisse, darunter "
            "Hitzewellen, Starkregen und Dürren. Die Modelle deuten darauf hin, dass anthropogene "
            "Emissionen der Haupttreiber dieser Veränderungen sind."
        ),
        "meta": {
            "doi": "10.1126/science.abc1234",
            "authors": ["Müller, T.", "Johnson, L."],
            "year": 2021,
            "journal": "Science",
            "peer_reviewed": True,
            "topics": ["Klimawandel", "Extremwetter"],
        },
    },
    {
        "external_id": "doi:10.1038/nature2345",
        "title": "Neural Mechanisms of Memory Consolidation",
        "text": (
            "Diese Arbeit untersucht neuronale Aktivitätsmuster während der Gedächtniskonsolidierung. "
            "Mittels fMRT und Netzwerkanalyse konnten spezifische Hippocampus-Kortex-Interaktionen "
            "identifiziert werden, die mit stabileren Erinnerungsspuren einhergehen."
        ),
        "meta": {
            "doi": "10.1038/nature2345",
            "authors": ["Schneider, A.", "Lee, K."],
            "year": 2022,
            "journal": "Nature",
            "peer_reviewed": True,
            "topics": ["Neurowissenschaft", "Gedächtnis"],
        },
    },
    {
        "external_id": "arxiv:2401.01234",
        "title": "Large Language Models as Scientific Assistants: A Systematic Evaluation",
        "text": (
            "Wir evaluieren die Fähigkeiten großer Sprachmodelle bei wissenschaftlichen Aufgaben wie "
            "Literaturrecherche, Methodenauswahl und Ergebnisinterpretation. Die Ergebnisse zeigen, "
            "dass aktuelle Modelle häufig plausibel klingende, aber falsche Aussagen generieren, "
            "wenn sie keine verlässlichen Quellen erhalten."
        ),
        "meta": {
            "source": "arXiv",
            "year": 2024,
            "peer_reviewed": False,
            "topics": ["KI", "Wissenschaftsjournalismus", "LLM"],
        },
    },
    {
        "external_id": "doi:10.1016/j.cell.2020.02.015",
        "title": "Microbiome Interactions in the Human Gut",
        "text": (
            "Die Untersuchung des menschlichen Darmmikrobioms zeigt, dass bestimmte Bakterienstämme "
            "eng mit Immunreaktionen verknüpft sind. Ernährungsmuster hatten dabei größere Auswirkungen "
            "als zuvor angenommen, insbesondere im Hinblick auf entzündliche Erkrankungen."
        ),
        "meta": {
            "doi": "10.1016/j.cell.2020.02.015",
            "authors": ["Garcia, M.", "Zhou, Y."],
            "year": 2020,
            "journal": "Cell",
            "peer_reviewed": True,
            "topics": ["Mikrobiom", "Immunologie"],
        },
    },
    {
        "external_id": "press:esa_mars_mission",
        "title": "ESA Announces New Mars Exploration Mission for 2032",
        "text": (
            "Die Europäische Weltraumorganisation (ESA) hat eine neue Mission zur Erforschung des Mars angekündigt. "
            "Das Vorhaben soll geologische Proben sammeln und mögliche Hinweise auf vergangene mikrobielle Aktivität "
            "untersuchen. Die Mission ist Teil eines langfristigen Programms zur Erforschung des Sonnensystems."
        ),
        "meta": {
            "source": "ESA Press Release",
            "year": 2023,
            "peer_reviewed": False,
            "topics": ["Raumfahrt", "Mars"],
        },
    },
    {
        "external_id": "doi:10.1186/s12916-021-02234-y",
        "title": "Long COVID Symptoms and Their Predictors",
        "text": (
            "In einer Kohortenstudie mit über 3000 Teilnehmenden wurden die häufigsten Long-COVID-Symptome "
            "identifiziert. Fatigue, kognitive Störungen und Atemnot traten besonders häufig auf. "
            "Risikofaktoren umfassten ein höheres Alter und mehrere Vorerkrankungen."
        ),
        "meta": {
            "doi": "10.1186/s12916-021-02234-y",
            "authors": ["Rojas, P.", "Smith, J."],
            "year": 2021,
            "journal": "BMC Medicine",
            "peer_reviewed": True,
            "topics": ["COVID-19", "Long-COVID"],
        },
    },
    {
        "external_id": "arxiv:2311.12345",
        "title": "RAG Architectures for Reliable Retrieval in Scientific Domains",
        "text": (
            "Wir analysieren unterschiedliche RAG-Architekturen in wissenschaftlichen Kontexten. "
            "Im Vergleich zu einfachen BM25-Methoden zeigt sich, dass Re-Ranking und Kontextfilter "
            "die Robustheit der Antworten erheblich verbessern und Halluzinationen reduzieren können."
        ),
        "meta": {
            "source": "arXiv",
            "year": 2023,
            "peer_reviewed": False,
            "topics": ["RAG", "Information Retrieval", "Wissenschaft"],
        },
    },
    {
        "external_id": "doi:10.1103/physrevlett.129.123456",
        "title": "Quantum Entanglement Observed in Macroscopic Systems",
        "text": (
            "Forscher konnten Quantenverschränkung erstmals in einem makroskopischen mechanischen Resonator "
            "nachweisen. Dieser Durchbruch eröffnet neue Perspektiven für Quantenkommunikation und "
            "präzise Messverfahren auf makroskopischer Skala."
        ),
        "meta": {
            "doi": "10.1103/physrevlett.129.123456",
            "authors": ["Weber, L.", "Nguyen, H."],
            "year": 2023,
            "journal": "Physical Review Letters",
            "peer_reviewed": True,
            "topics": ["Quantenphysik"],
        },
    },
    {
        "external_id": "report:oecd_energy_2024",
        "title": "OECD Energy Outlook 2024: Global Trends",
        "text": (
            "Der OECD-Energiebericht 2024 prognostiziert einen deutlichen Anstieg erneuerbarer Energien "
            "in industriellen Nationen. Fossile Brennstoffe werden jedoch weiterhin bis mindestens 2040 "
            "einen relevanten Anteil am Energiemix ausmachen."
        ),
        "meta": {
            "source": "OECD Report",
            "year": 2024,
            "peer_reviewed": False,
            "topics": ["Energie", "Klimapolitik"],
        },
    },
    {
        "external_id": "doi:10.1177/0956797624123456",
        "title": "Social Media Use Correlates With Reduced Sleep in Adolescents",
        "text": (
            "Eine psychologische Studie zeigt, dass Jugendliche, die mehr als drei Stunden täglich Social Media "
            "nutzen, signifikant weniger Schlaf erhalten. Mögliche Mechanismen umfassen kognitive Übererregung "
            "und nächtliche Benachrichtigungen durch mobile Endgeräte."
        ),
        "meta": {
            "doi": "10.1177/0956797624123456",
            "authors": ["Kim, S.", "Wagner, F."],
            "year": 2024,
            "journal": "Psychological Science",
            "peer_reviewed": True,
            "topics": ["Psychologie", "Schlaf"],
        },
    },
    {
        "external_id": "doi:10.1093/eurheartj/ehad001",
        "title": "Impact of Air Pollution on Cardiovascular Health",
        "text": (
            "Die Studie untersucht den Zusammenhang zwischen Feinstaubbelastung und kardiovaskulären Ereignissen "
            "in europäischen Großstädten. Höhere PM2.5-Konzentrationen waren mit einem erhöhten Risiko für "
            "Herzinfarkte und Schlaganfälle assoziiert."
        ),
        "meta": {
            "doi": "10.1093/eurheartj/ehad001",
            "authors": ["Keller, J.", "Rodriguez, M."],
            "year": 2023,
            "journal": "European Heart Journal",
            "peer_reviewed": True,
            "topics": ["Kardiologie", "Luftverschmutzung"],
        },
    },
    {
        "external_id": "arxiv:2305.09876",
        "title": "Benchmarking RAG Systems for Climate Science Communication",
        "text": (
            "Wir benchmarken verschiedene RAG-Systeme in der Kommunikation von Klimawissenschaft. "
            "Dabei wird gemessen, wie gut Modelle komplexe Fachbegriffe erklären, Unsicherheiten kennzeichnen "
            "und zentrale Aussagen korrekt wiedergeben."
        ),
        "meta": {
            "source": "arXiv",
            "year": 2023,
            "peer_reviewed": False,
            "topics": ["RAG", "Klimawissenschaft", "Kommunikation"],
        },
    },
    {
        "external_id": "doi:10.1002/eji.202345678",
        "title": "Novel Biomarkers for Early Detection of Autoimmune Diseases",
        "text": (
            "Die Arbeit identifiziert mehrere zirkulierende Biomarker, die mit dem frühen Stadium "
            "autoimmuner Erkrankungen assoziiert sind. Eine Kombination aus Proteomik-Analysen "
            "und maschinellem Lernen ermöglichte eine verbesserte Risikostratifizierung."
        ),
        "meta": {
            "doi": "10.1002/eji.202345678",
            "authors": ["Lange, P.", "Singh, R."],
            "year": 2024,
            "journal": "European Journal of Immunology",
            "peer_reviewed": True,
            "topics": ["Immunologie", "Biomarker"],
        },
    },
    {
        "external_id": "press:who_ultra_processed_foods",
        "title": "WHO Warns About Health Risks of Ultra-Processed Foods",
        "text": (
            "Die Weltgesundheitsorganisation (WHO) warnt vor den langfristigen Gesundheitsrisiken "
            "stark verarbeiteter Lebensmittel. Sie empfiehlt Regierungen, klare Kennzeichnungen "
            "und Beschränkungen für Werbung gegenüber Kindern einzuführen."
        ),
        "meta": {
            "source": "WHO Press Release",
            "year": 2023,
            "peer_reviewed": False,
            "topics": ["Ernährung", "Public Health"],
        },
    },
    {
        "external_id": "doi:10.1088/1748-9326/acf789",
        "title": "Urban Heat Islands and Social Inequality",
        "text": (
            "Die Studie zeigt, dass sozial benachteiligte Stadtviertel stärker von urbanen Hitzeinseln "
            "betroffen sind. Fehlende Grünflächen und dichte Bebauung verstärken das Risiko "
            "hitzebedingter Gesundheitsprobleme."
        ),
        "meta": {
            "doi": "10.1088/1748-9326/acf789",
            "authors": ["Ahmed, Y.", "Kowalski, D."],
            "year": 2023,
            "journal": "Environmental Research Letters",
            "peer_reviewed": True,
            "topics": ["Stadtklima", "Soziale Ungleichheit"],
        },
    },
    {
        "external_id": "arxiv:2209.04567",
        "title": "Evaluating Fact-Checking Pipelines for Science Journalism",
        "text": (
            "Wir vergleichen automatisierte Fact-Checking-Pipelines für wissenschaftsjournalistische Artikel. "
            "Besonders kritisch sind fehlerhafte Zuordnungen von Studienergebnissen und fehlende Kontextangaben, "
            "die zu verzerrten Schlagzeilen führen können."
        ),
        "meta": {
            "source": "arXiv",
            "year": 2022,
            "peer_reviewed": False,
            "topics": ["Faktenprüfung", "Wissenschaftsjournalismus"],
        },
    },
    {
        "external_id": "doi:10.1111/jcpp.13654",
        "title": "Screen Time and Cognitive Development in Early Childhood",
        "text": (
            "Die Studie untersucht den Zusammenhang von Bildschirmzeit und kognitiver Entwicklung "
            "bei Kindern im Vorschulalter. Moderate Nutzung zeigte keine negativen Effekte, "
            "während exzessive Nutzung mit Sprachverzögerungen assoziiert war."
        ),
        "meta": {
            "doi": "10.1111/jcpp.13654",
            "authors": ["Novak, E.", "Hansen, G."],
            "year": 2022,
            "journal": "Journal of Child Psychology and Psychiatry",
            "peer_reviewed": True,
            "topics": ["Entwicklungspsychologie", "Mediennutzung"],
        },
    },
    {
        "external_id": "report:ipcc_synthesis_2023",
        "title": "IPCC Synthesis Report 2023: Key Messages",
        "text": (
            "Der IPCC-Synthesebericht 2023 fasst den aktuellen Stand der Klimaforschung zusammen. "
            "Er betont die Dringlichkeit schneller Emissionsreduktionen und warnt vor dem Überschreiten "
            "kritischer Kipppunkte im Klimasystem."
        ),
        "meta": {
            "source": "IPCC Report",
            "year": 2023,
            "peer_reviewed": False,
            "topics": ["Klimawandel", "IPCC"],
        },
    },
    {
        "external_id": "doi:10.1098/rsos.2023456",
        "title": "Public Understanding of Scientific Uncertainty in Pandemic Reporting",
        "text": (
            "Die Autoren analysieren, wie gut Öffentlichkeit und Medien wissenschaftliche Unsicherheit "
            "während einer Pandemie verstehen. Vage Formulierungen und fehlende Erklärungen statistischer "
            "Begriffe führten häufig zu Fehlinterpretationen."
        ),
        "meta": {
            "doi": "10.1098/rsos.2023456",
            "authors": ["Brown, C.", "Yilmaz, O."],
            "year": 2023,
            "journal": "Royal Society Open Science",
            "peer_reviewed": True,
            "topics": ["Wissenschaftskommunikation", "Pandemie"],
        },
    },
    {
        "external_id": "arxiv:2402.06789",
        "title": "Calibrating LLM Responses for Responsible Science Communication",
        "text": (
            "Der Beitrag schlägt Methoden vor, um Antworten großer Sprachmodelle für die "
            "Wissenschaftskommunikation zu kalibrieren. Dazu zählen Unsicherheitsmarkierungen, "
            "Quellenpflicht und die explizite Kennzeichnung von Spekulation."
        ),
        "meta": {
            "source": "arXiv",
            "year": 2024,
            "peer_reviewed": False,
            "topics": ["LLM", "Wissenschaftskommunikation", "Ethik"],
        },
    },
]
