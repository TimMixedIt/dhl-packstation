# DHL Packstation – Beta installieren

Version: **0.2.0b2**, benötigt **Home Assistant 2026.10.4 oder neuer**.

## Über Marketplace / HACS

Unter „Benutzerdefinierte Repositories“ die URL **https://github.com/TimMixedIt/dhl-packstation** mit Kategorie **Integration** hinzufügen und herunterladen. Danach HA neu starten und unter Geräte & Dienste „DHL Packstation“ hinzufügen. Falls du ausdrücklich die markierte Beta-Version auswählen möchtest, Vorabversionen anzeigen lassen; alternativ ist der Standardzweig `main` installierbar.

## Manuell über ZIP

1. Ein Backup deiner Home-Assistant-Konfiguration erstellen.
2. Das Installations-ZIP entpacken.
3. Den enthaltenen Ordner `custom_components/dhl_packstation` in deinen HA-Konfigurationsordner kopieren. Der fertige Pfad muss `<HA-Konfigurationsordner>/custom_components/dhl_packstation/manifest.json` enthalten. Es darf kein zusätzlicher Unterordner `dhl-packstation` dazwischenliegen.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **DHL Packstation** suchen.
6. Die Postleitzahl des Stationsstandorts und die Packstationsnummer eingeben.

Die Integration erzeugt ein Gerät pro Station mit vier Fachzahlsensoren für S/M/L/XL sowie zwei Diagnosewerten: DHL-Datenstand und „DHL-Daten veraltet oder fehlend“. Weitere Stationen werden durch erneutes Hinzufügen der Integration eingerichtet.

## Die mitgelieferten Karten

Nach der Einrichtung den Browser einmal neu laden. Dann im Dashboard „Bearbeiten → Karte hinzufügen“ öffnen:

- **DHL Packstation · Freie Fächer** für die Darstellung einer Station wie im DHL-Bild.
- **DHL Packstation · Mehrere Stationen** für den Vergleich mehrerer Stationen.

Die Karte im visuellen Editor auswählen und die Station(en) einstellen. Ohne Auswahl zeigt die Übersicht alle eingerichteten Stationen. „Genaue Fachzahlen anzeigen“ ersetzt „viele frei“ durch die konkrete Zahl. Ein Klick auf eine Fachgröße öffnet deren Sensorinformationen. Es ist kein zusätzliches Karten-Repository und kein manueller Ressourceneintrag nötig. Vorhandene Dashboards werden nicht automatisch verändert.

Die Abfrage erfolgt gemeinsam alle 15 Minuten. Unter den Optionen kannst du das maximale Alter der DHL-Daten festlegen. Standard sind 60 Minuten. Danach werden Fachzahlen nicht verfügbar, bis DHL wieder hinreichend aktuelle Daten liefert. Ein echter Nullwert bedeutet dagegen, dass DHL null freie Fächer dieser Größe gemeldet hat.

Falls du das frühere YAML-Beispiel installiert hast: Nach erfolgreichem Vergleich die dortigen REST-Sensoren selbst entfernen, wenn du sie nicht mehr brauchst. Sie werden nicht automatisch übernommen oder gelöscht.

Für ein Update den bisherigen Komponentenordner sichern, durch den neuen ersetzen und HA neu starten. Bei Problemen den gesicherten Ordner zurückkopieren und erneut starten. Zum Entfernen zuerst die Integrationseinträge in HA löschen, dann den Komponentenordner entfernen und HA neu starten.

Diese Beta ist als benutzerdefiniertes Repository verfügbar, aber noch nicht in den allgemeinen Marketplace-Katalog aufgenommen. Der nächste Schritt ist der [Praxistest](TESTPLAN_DE.md).
