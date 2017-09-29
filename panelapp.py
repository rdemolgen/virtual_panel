import requests, argparse, csv

# Argument Parser - Takes multiple panel names or no parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--evidence_level", default= "Amber", help = "Minimum evidence level to include (Green, Amber, Red)")
parser.add_argument('panel_names', nargs = '*', help = 'PanelApp panel names (in quotes)')
args = parser.parse_args()

if args.evidence_level.lower() == "red":
    evidence = "HighEvidence,ModerateEvidence,LowEvidence"
elif args.evidence_level.lower() == "green":
    evidence = "HighEvidence"
else:
    evidence = "HighEvidence,ModerateEvidence"

# Initalise dictionary to store gene list and panels
gene_dict = {}
panel_details = {}

def get_panels():
    panels = []
    # Get panel information from PanelApp API in json format
    server = "https://panelapp.extge.co.uk/crowdsourcing/WebServices/list_panels"
    r = requests.get(server, headers={ "Content-Type" : "application/json"})

    if not r.ok:
        r.raise_for_status()
        sys.exit()

    decoded = r.json()

    # Add all found panel names to list and print in alphabetical order
    for i in decoded['result']:
        panels.append(i['Name'])
    print("\n".join(sorted((panels), key = str.lower)))


def get_panel_version(panel_name):
    # Get gene information for panel(s) from PanelApp API in json format
    server = "https://panelapp.extge.co.uk/crowdsourcing/WebServices/get_panel/"
    ext = panel_name + "/?LevelOfConfidence=" + evidence
    r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})
    
    if not r.ok:
        r.raise_for_status()
        sys.exit()
    
    decoded = r.json()
    return decoded['result']['version']


def get_genelist(panel_name):
    # Get gene information for panel(s) from PanelApp API in json format
    server = "https://panelapp.extge.co.uk/crowdsourcing/WebServices/get_panel/"
    ext = panel_name + "/?LevelOfConfidence=" + evidence
    r = requests.get(server+ext, headers={ "Content-Type" : "application/json"})
    
    if not r.ok:
        r.raise_for_status()
        sys.exit()
    
    decoded = r.json()

    # For each gene, check symbol is current HGNC approved and add to dictionary (to ensure unique list)
    for i in decoded['result']['Genes']:
        valid = check_HGNC(i['GeneSymbol'])
        gene_dict.update({i['GeneSymbol']:[i['ModeOfInheritance'], valid]})


def check_HGNC(gene_symbol):
    # Get gene information from HGNC API in json format
    server = "http://rest.genenames.org/fetch/symbol/"
    ext = str(gene_symbol)
    r = requests.get(server+ext, headers={ "Accept" : "application/json"})

    if not r.ok:
        r.raise_for_status()
        sys.exit()

    decoded = r.json()

    # See if gene name exists, if not try to look up as a previous name and return current or report a non-valid HGNC symbol
    try:
        decoded['response']['docs'][0]['symbol']
    except:
        # Get gene information from HGNC API in json format
        server = "http://rest.genenames.org/fetch/prev_symbol/"
        ext = str(gene_symbol)
        r = requests.get(server+ext, headers={ "Accept" : "application/json"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        decoded = r.json()

        try:
            decoded['response']['docs'][0]['symbol']
            return(decoded['response']['docs'][0]['symbol'])
        except:
            return("Not a valid HGNC symbol")


if __name__ == '__main__':
    # If panel names are supplied as arguments, collect gene information
    if args.panel_names:
        args = vars(parser.parse_args())
        for i in args['panel_names']:
            panel_details.update({i:get_panel_version(i)})
            get_genelist(i)
        
        # Format panel string
        versions = "Gene list: PanelApp ("
        for key, value in panel_details.items():
            versions += key + " v" + value + ", "     
        versions = versions[0:-2]
        versions += ")"

        # Write required gene names and additional information to alphabetically sorted csv file
        with open('gene_list.csv', 'w') as f:
            w = csv.writer(f)
            w.writerow(["gene", "inheritance", "Suggested gene names", "", versions])
            for key in sorted(gene_dict.keys()):
                w.writerow([key] + gene_dict[key])
    # Otherwise return a list of available panel names
    else:
        get_panels()
