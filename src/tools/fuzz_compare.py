from thefuzz import fuzz, process

if __name__ == "__main__":
    collection = [
        "GREAT CAESAR! HE'S TOUGHER\nTHAN A BUCKET OF\nBOLTS!",
        "HE BREAKS THE TEETH OFF\nOF THE SAW!",
        "RASP!",
        "HE WON'T EVEN\nGRIND INTO HASH!",
        "HELLO! IS THIS\nTHE JIFFY POULTRY\nCLEANING PLANT?",
        "YESSIR!",
        "I SHOULDN'T\nWONDER THAT\nHE IS TOUGH,\nMISTER!",
        "WELL, I WANT TO KNOW WHAT YOU DID\nTO THAT TURKEY I BROUGHT\nYOU IN A SACK LAST NIGHT!\nHE'S TOUGHER THAN\nIRON!",
        "YOU SEE, YOU WERE BADLY\nMISTAKEN ABOUT THAT BIRD!\nBUT I CAN TELL YOU WHAT'S\nWRONG WITH HIM IN\nA VERY FEW WORDS!",
        "HE JUST WASN'T A TURKEY,\nBROTHER — HE\nWAS AN\nEAGLE!",
        "YE OLDE DINING CAR\nTURKEY\nDINNER\n$2.50 A PLATE\nDESSERT\nEXTRA",
    ]

    text = "TURKEY\nDINNER\n$2.50 A PLATE\nDESSERT\nEXTRA"

    similarity_scores = process.extract("barcelona", collection, scorer=fuzz.ratio)
