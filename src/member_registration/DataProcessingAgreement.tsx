import { COOP_NAME, COOP_STREET, COOP_PLACE } from "./constants";

export default function DataProcessingAgreement() {
  return (
    <details className="ms-4 mt-2">
      <summary>Datenschutzerklärung</summary>
      <p>
        Verantwortlich für die Datenverarbeitung ist die {COOP_NAME},{" "}
        {COOP_STREET}, {COOP_PLACE}. Erreichbar unter contact@supercoop.de. Der
        Name, die Anschrift und das Geburtsdatum werden für die Mitgliederliste
        der Genossenschaft benötigt (Art. 6 Absatz 1 c DS-GVO i.V.m. §30 Absatz
        2 Satz 1 Nr.1 GenG). Über die Adresse oder die E-Mail-Adresse werden Sie
        von der Genossenschaft zu Versammlungen eingeladen (Art. 6 Absatz 1c
        DS-GVO i.V.m §46 Absatz 1 Satz 1 GenG i.V.m. §6 Nr.4 GenG) und im Rahmen
        der Mitgliedschaft über Angebote der Genossenschaft informiert (Art.6
        Absatz 1 b DS-GVO i.V.m. §1 Absatz 1 GenG i.V.m. der Satzung). Die
        Genossenschaft hat ein berechtigtes Interesse an einer unkomplizierten
        und rechtssicheren Erfüllung ihrer Verbindlichkeiten. Die Bereitstellung
        der personenbezogenen Daten ist gesetzlich bzw. durch die Satzung
        vorgeschrieben, die Nichtbereitstellung hätte zur Folge, dass die
        Mitgliedschaft nicht zustande kommen kann.
      </p>
      <p>
        Die personenbezogenen Daten werden nicht an Dritte weitergeleitet,
        soweit nicht im Einzelfall dafür eine Einwilligung erteilt wird. Wir
        sind allerdings gesetzlich verpflichtet, in einigen Fällen Dritten die
        Einsicht in die personenbezogenen Daten zu gewähren. Das betrifft zum
        Beispiel andere Mitglieder, den gesetzlichen Prüfungsverband oder
        Behörden, insbesondere das Finanzamt. Die Daten werden unterschiedlich
        aufbewahrt: Alle steuerlich relevanten Informationen werden zehn Jahre
        aufbewahrt (§147 AO). Die Daten in der Mitgliederliste (Name und
        Anschrift nach §30 Absatz 2 Satz 1 Nr. 1 GenG) werden auch nach dem
        Ausscheiden nicht gelöscht (§30 Absatz 2 Satz 1 Nr. 3 GenG). Sie haben
        das Recht auf Auskunft seitens des Verantwortlichen über die
        betreffenden personenbezogenen Daten sowie auf Berichtigung oder
        Löschung oder auf Einschränkung der Verarbeitung (soweit dem nicht eine
        gesetzliche Regelung entgegensteht). Auch kann eine Datenübertragung
        angefordert werden, sollte der Unterzeichnende eine Übertragung seiner
        Daten an eine dritte Stelle wünschen. Darüber hinaus haben Sie das Recht
        auf Beschwerde bei einer Aufsichtsbehörde (Landesbeauftragte für
        Datenschutz).
      </p>
    </details>
  );
}
