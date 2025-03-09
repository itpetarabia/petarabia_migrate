def format_pet_name(pets):
    if len(pets) == 1:
        return pets[0].name
    if len(pets) == 2:
        return f'{pets[0].name} & {pets[1].name}'
    if len(pets) > 2:
        petnames = ", ".join([p.name for p in pets[:-1]])
        return petnames + " & " + pets[-1].name