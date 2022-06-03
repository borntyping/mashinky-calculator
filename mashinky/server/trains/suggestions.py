WAGON_SUGGESTIONS: dict[str, list[list[str]]] = {
    "Coach car": [
        ["1st Class", "Pwg PR-14"],
        ["1st Class"],
        ["Pwg PR-14"],
    ],
    "1st Class": [
        ["2nd class", "Pwg PR-14"],
        ["Dining car", "Pwg PR-14"],
        ["2nd class"],
        ["Dining car"],
        ["Pwg PR-14"],
    ],
    "2nd class": [
        ["1st Class", "Pwg PR-14"],
        ["Dining car", "Pwg PR-14"],
        ["1st Class"],
        ["Dining car"],
        ["Pwg PR-14"],
    ],
    "SCF": [
        ["SCF Diner", "SCF Mail"],
        ["SCF Diner"],
        ["SCF Mail"],
    ],
    "SCG": [
        ["SCG Diner", "SCF Mail"],
        ["SCG Diner"],
        ["SCG Mail"],
    ],
    "SGV class 1": [
        ["SGV Diner", "SCF Mail"],
        ["SGV Diner"],
        ["SGV Mail"],
    ],
    "SGV class 2": [
        ["SGV class 1", "SCF post"],
        ["SGV bar", "SCF post"],
        ["SGV class 1"],
        ["SGV bar"],
        ["SGV post"],
    ],
}
