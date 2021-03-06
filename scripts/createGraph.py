#!/usr/bin/env python3
#
# pip3 install matplotlib

from matplotlib import pyplot as plt
from dateutil import parser
from statistics import mean
import datetime
import json
import modules.brondata as brondata


brondata.freshdata()
metenisweten = brondata.readjson('../cache/daily-stats.json')

print("Calculating predictions...")

positief = {
    'x': [],
    'y': []
}

opgenomen = {
    'x': [],
    'y': []
}

positief_gemiddeld = {
    'x': [],
    'y': [],
    'avgsize': 14
}

positief_voorspeld = {
    'x': [],
    'y': [],
    'avgsize': 12
}

geschat_ziek = {
    'x'   : [],
    'y'   : [],
    'min' : [],
    'max' : []
}

ic = {
    'x' : [],
    'y' : [],
    'rc' : []
}

ic_voorspeld = {
    'x' : [],
    'y' : [],
    'avgsize': 3
}

besmettingsgraad = {
    'x' : [],
    'y' : []    
}

# print("2020-01-30")
# print((parser.parse("2020-01-30") - datetime.timedelta(days=ziekteduur)).strftime("%Y-%m-%d"))
# exit

date_range = brondata.getDateRange(metenisweten)

for d in date_range:
    datum = d.strftime("%Y-%m-%d")

    # --------------------------------- Normale grafieken (exclusief data van vandaag want dat is altijd incompleet)
    if datum in metenisweten and parser.parse(datum).date() <= datetime.date.today():
        positief['x'].append(parser.parse(datum))
        positief['y'].append(metenisweten[datum]['positief'])

        ic['x'].append(parser.parse(datum))
        ic['y'].append(metenisweten[datum]['nu_op_ic'])

        opgenomen['x'].append(parser.parse(datum))
        opgenomen['y'].append(metenisweten[datum]['opgenomen'])

        totaal_positief = metenisweten[datum]['totaal_positief']

        if metenisweten[datum]['rivm-datum']:
            filedate = metenisweten[datum]['rivm-datum']

        if len(ic['y'])>1:
            ic['rc'].append(ic['y'][-1] - ic['y'][-2])
        else:
            ic['rc'].append(0)

    # --------------------------------- Gemiddeld positief getest
    if datum in metenisweten:
        avg = mean(positief['y'][len(positief['y'])-11:])
    else:
        avg = mean(positief_gemiddeld['y'][len(positief_gemiddeld['y'])-11:])
    positief_gemiddeld['x'].append(parser.parse(datum) - datetime.timedelta(days=positief_gemiddeld['avgsize']/2))
    positief_gemiddeld['y'].append(avg)

    # ---------------------- Voorspelling positief getst obv gemiddelde richtingscoefficient positief getest.
    if datum in metenisweten and len(positief['y']) > positief_voorspeld['avgsize'] and parser.parse(datum) < (datetime.datetime.now() - datetime.timedelta(days=positief_voorspeld['avgsize'])):
        # Voorspel morgen op basis van metingen
        rc = (positief['y'][-1]-positief['y'][-positief_voorspeld['avgsize']]) / positief_voorspeld['avgsize']
        positief_voorspeld['x'].append(parser.parse(datum) + datetime.timedelta(days=1))
        positief_voorspeld['y'].append(positief['y'][-1] + rc)
    elif len(positief_voorspeld['y']) > positief_voorspeld['avgsize']:
        # Voorspel morgen op basis van schatting gisteren
        rc = (positief_voorspeld['y'][-1]-positief_voorspeld['y'][-positief_voorspeld['avgsize']]) / positief_voorspeld['avgsize']
        positief_voorspeld['x'].append(parser.parse(datum) + datetime.timedelta(days=1))
        positief_voorspeld['y'].append(positief_voorspeld['y'][-1] + rc)
    else:
        # If all else fails neem waarde van vorige positief
        positief_voorspeld['x'].append(parser.parse(datum) + datetime.timedelta(days=1))
        positief_voorspeld['y'].append(positief['y'][-1])


    # ---------------------- Voorspelling op IC obv gemiddelde richtingscoefficient positief getest.
    if len(ic['x']) > 10 and parser.parse(datum) > ic['x'][-1]:
        ic_rc = mean(ic['rc'][-5:])

        ic_voorspeld['x'].append(parser.parse(datum))
        ic_voorspeld['y'].append(ic['y'][-1] + ic_rc * (parser.parse(datum) - ic['x'][-1]).days )

    # ----------------------- Trek "geschat ziek" op basis van RC nog even door.
    deltadagen = 15
    if datum in metenisweten and metenisweten[datum]['rivm_schatting_besmettelijk']['value']:
        geschat_ziek['x'].append(parser.parse(datum))
        geschat_ziek['y'].append(metenisweten[datum]['rivm_schatting_besmettelijk']['value'])
        geschat_ziek['min'].append(metenisweten[datum]['rivm_schatting_besmettelijk']['min'])
        geschat_ziek['max'].append(metenisweten[datum]['rivm_schatting_besmettelijk']['max'])
        geschat_ziek_nu = metenisweten[datum]['rivm_schatting_besmettelijk']['value']
    elif len(geschat_ziek['y']) > deltadagen:
        vorig_datum = parser.parse(datum) - datetime.timedelta(days=deltadagen)
        vorig_y = geschat_ziek['y'][-deltadagen]
        nieuw_y = geschat_ziek['y'][-1] + (geschat_ziek['y'][-1] - vorig_y)/deltadagen
        geschat_ziek['x'].append(parser.parse(datum))
        geschat_ziek['y'].append(nieuw_y)


def decimalstring(number):
    return "{:,}".format(number).replace(',','.')


def anotate(plt, metenisweten, datum, tekst, x, y):
    if datum in metenisweten:
        plt.annotate(
            tekst,
            xy=(parser.parse(datum), metenisweten[datum]['positief']),
            xytext=(parser.parse(x), y),
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.4', fc='ivory', alpha=1),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1')
        )

print('Generating daily positive tests graph...')

fig, ax1 = plt.subplots(figsize=(10, 5))
fig.subplots_adjust(top=0.92, bottom=0.13, left=0.09, right=0.91)

ax2 = plt.twinx()

#plt.figure(figsize =(10,5))
ax1.grid(which='both', axis='both', linestyle='-.',
         color='gray', linewidth=1, alpha=0.3)
ax2.grid(which='both', axis='both', linestyle='-.',
         color='gray', linewidth=1, alpha=0.3)

# Plot cases per dag
ax1.plot(positief['x'][:-10], positief['y'][:-10], color='steelblue', label='positief getest (totaal '+decimalstring(totaal_positief)+")")
ax1.plot(positief['x'][-11:], positief['y'][-11:], color='steelblue', linestyle='--', alpha=0.3, label='onvolledig')

anotate(ax1, metenisweten, "2020-03-09",
        'Brabant geen\nhanden schudden', "2020-02-05", 300)
anotate(ax1, metenisweten, "2020-03-15",
        'Onderwijs,\nverpleeghuis,\nhoreca\ndicht', "2020-02-05", 600)
anotate(ax1, metenisweten, "2020-03-23",
        '1,5 meter, €400 boete', "2020-02-05", 1000)
anotate(ax1, metenisweten, "2020-05-11", 'Scholen 50% open,\nkappers open', "2020-03-25", 100)
anotate(ax1, metenisweten, "2020-06-01", 'Terrassen open,\ntests voor\niedereen', "2020-05-02", 800)
anotate(ax1, metenisweten, "2020-06-08",
        'Scholen\nopen', "2020-06-01", 350)
anotate(ax1, metenisweten, "2020-07-01",
        'Maatregelen afgezwakt,\nalleen nog 1,5 meter,\nmondkapje in OV', "2020-05-25", 550)
anotate(ax1, metenisweten, "2020-07-04",
        'Begin\nschoolvakanties', "2020-06-25", 350)
anotate(ax1, metenisweten, "2020-08-06",
        'Meer bevoegdheden\ngemeenten.\nContactgegevens aan\nrestaurant afgeven.\nTesten op Schiphol.', "2020-07-01", 820)
anotate(ax1, metenisweten, "2020-08-24",
        'Einde\nschoolvakanties', "2020-08-10", 320)
anotate(ax1, metenisweten, "2020-09-01",
        'Ophef bruiloft\nGrapperhaus', "2020-08-10", 1150)
anotate(ax1, metenisweten, "2020-09-20",
        'www.ballonvossenjacht.nl\nKroegen sluiten om 00:00,\nlokale maatregelen\nWest NL', "2020-08-12", 720)


ax1.text(parser.parse("2020-05-20"), 1215, "\"Misschien ben jij klaar met het virus,\n   maar het virus is niet klaar met jou.\"\n    - Hugo de Jonge", color="gray")

# Plot average per dag
# ax1.plot(positief_gemiddeld['x'], positief_gemiddeld['y'], color='cyan', linestyle=':',
#          label=str(positief_gemiddeld['avgsize'])+' daags gemiddelde, t-' +
#          str(int(positief_gemiddeld['avgsize']/2))
#          )

ax1.plot(positief_voorspeld['x'][-20:], positief_voorspeld['y'][-20:], 
         color='steelblue', linestyle=':', label='voorspeld')

nu_op_ic = ic['y'][-1]
ax1.plot(ic['x'], ic['y'], color='red', label='aantal op IC (nu: '+decimalstring(nu_op_ic)+')')
ax1.plot(ic_voorspeld['x'], ic_voorspeld['y'], color='red', linestyle=':')

# ax1.plot(opgenomen['x'], opgenomen['y'], color='green',
#          linestyle='-', label='opgenomen (totaal: '+decimalstring(totaal_opgenomen)+')')

# ax2.plot(ziek['x'], ziek['y'], color='darkorange',
#          linestyle=':', label='geschat besmettelijk (nu: '+decimalstring(geschat_besmettelijk)+')')

# Test for plotting besmettelijk op basis van rna
ax2.plot(geschat_ziek['x'], geschat_ziek['y'], color='darkorange',
         linestyle=':', label='RIVM schatting totaal ziek (nu: '+decimalstring(round(geschat_ziek_nu))+')')
ax2.fill_between(geschat_ziek['x'][:len(geschat_ziek['min'])], geschat_ziek['min'], geschat_ziek['max'],facecolor='darkorange', alpha=0.1, interpolate=True)


# laat huidige datum zien met vertikale lijn
ax2.axvline(positief['x'][-1], color='teal', linewidth=0.15)

# Horizontale lijn om te checken waar we de IC opnames mee kunnen vergelijken
ax1.axhline(ic['y'][-1], color='red', linestyle=(0, (5, 30)), linewidth=0.2)

ax1.set_xlabel("Datum")
ax1.set_ylabel("Aantal positief / op IC")
ax2.set_ylabel("Geschat besmettelijk")

ax1.set_ylim([0, 1600])
ax2.set_ylim([0, 1600 * 250])

plt.gca().set_xlim([parser.parse("2020-02-01"), ic_voorspeld['x'][-1]])

# ax1.set_yscale('log')
# ax2.set_yscale('log')

gegenereerd_op=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

plt.title('Positieve COVID-19 tests, '+gegenereerd_op)

footerleft="Gegenereerd op "+gegenereerd_op+".\nSource code: http://github.com/realrolfje/coronadata"
plt.figtext(0.01, 0.01, footerleft, ha="left", fontsize=8, color="gray")


footerright="Publicatiedatum RIVM "+filedate+".\nBronnen: https://data.rivm.nl/covid-19, https://www.stichting-nice.nl/covid-19/"
plt.figtext(0.99, 0.01, footerright, ha="right", fontsize=8, color="gray")


ax1.legend(loc="upper left")
ax2.legend(loc="upper right")
plt.savefig("../graphs/besmettingen.png", format="png")
plt.savefig("../graphs/besmettingen.svg", format="svg")
#plt.show()

print('Write text for tweet update in ../docs/tweet.txt')
with open("../docs/tweet.txt", 'w') as file:
    file.write(
        'Positief getest: '+decimalstring(totaal_positief)+' (RIVM)\n' +
        'Nu op IC: '+decimalstring(nu_op_ic)+' (NICE)\n' +
#        'Besmettelijk: '+decimalstring(geschat_besmettelijk)+' (geschat)\n' +
        'Geschat ziek: '+decimalstring(round(geschat_ziek_nu))+' (RIVM schatting)\n' +
        'https://realrolfje.github.io/coronadata/\n' +
        '#COVID19 #coronavirus'
    )
