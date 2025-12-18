from core.models import Home

print("=== EXISTING HOMES ===\n")
homes = Home.objects.all()
if homes:
    for home in homes:
        print(f"ID: {home.id}, Name: {home.name}, Owner: {home.owner.username}")
else:
    print("No homes found")
