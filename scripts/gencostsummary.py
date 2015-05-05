"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
import csv

import entityhub.projects
import gedaif.conffile

from utils.config import KOALA_ROOT


fpath = os.path.join(KOALA_ROOT, 'scratch', 'costing-summary.csv')
with open(fpath, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Card", "Indicative Cost"])
    for card, cardfolder in sorted(entityhub.projects.cards.iteritems()):
        cfg = gedaif.conffile.ConfigsFile(cardfolder)
        for configuration in cfg.configdata['configurations']:
            if configuration['configname'] == card:
                carddesc = configuration['desc']
        if carddesc is None:
            carddesc = ''
        cost = entityhub.projects.get_card_indicative_cost(card)
        if cost is not None:
            writer.writerow([card, round(cost), carddesc])
