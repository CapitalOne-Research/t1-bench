from src.t1_plus_plus.ontology.city import CITIES, city_neighborhoods_dict

LOCATIONS = CITIES[:]
NEIGHBORHOODS = city_neighborhoods_dict.copy()


VENUE_TYPES = {
    "concert": ["Arena", "Stadium", "Amphitheater", "Concert Hall", "Ballroom"],
    "play": ["Proscenium Theater", "Black Box Theater", "Thrust Stage Theater"],
    "musical": ["Proscenium Theater", "Performing Arts Center", "Grand Palace"],
    "opera": ["Opera House", "Lyric Theater"],
    "ballet": ["Opera House", "Performing Arts Center"],
    "standup comedy": ["Comedy Club", "Boutique Theater", "Jazz Club", "Black Box Theater"],
    "jazz": ["Jazz Club", "Concert Hall", "Intimate Lounge"],
    "circus show": ["Big Top Tent", "Arena", "Multipurpose Stadium"]
}


VENUE_NAMES = {
    "Arena": [
        "Apex Titan Arena", "Thunderstone Arena", "The Obsidian Bowl", 
        "Vertex Event Center", "Iron Pulse Arena", "The Zenith Ring", 
        "Echo Ridge Arena", "The Colossal Core", "Velocity Arena", 
        "Summit Indoor Grounds", "The Kinetic Dome", "Nova Strike Arena", 
        "The Bastion", "Aura Arena", "Titanium Field House"
    ],
    "Stadium": [
        "The Nova Skyline Stadium", "Vanguard Victory Field", "The Solar Flare Stadium", 
        "Pinnacle Park", "Horizon View Stadium", "The Grand Stand", 
        "Apex Athletics Grounds", "Silver Turf Stadium", "The Monolith", 
        "Beacon Bowl", "Emerald Valley Stadium", "The Sovereign Field", 
        "Legacy Stadium", "Crestline Grounds", "North Star Arena"
    ],
    "Amphitheater": [
        "The Whisperwind Amphitheater", "Oracle Outdoor Pavilion", "Sun-Drenched Stones", 
        "The Echo Canyon Stage", "Breeze-Way Bowl", "Starlight Shell", 
        "The Moonlit Slope", "Crestview Amphitheater", "Serenity Soundstage", 
        "The Open-Air Lyceum", "Wildflower Pavilion", "Stone Circle Stage", 
        "The Valley Amphitheater", "Ember Glow Pavilion", "Skybound Shell"
    ],
    "Concert Hall": [
        "Aurelian Symphony Hall", "Solstice Concert Hall", "The Archon Auditorium", 
        "Prism Philharmonic", "The Ivory Atrium", "Vibrance Hall", 
        "The Harmonic Wing", "Resonance Rooms", "The Coda Center", 
        "Lumina Concert Hall", "Classic Chord House", "The Orchestral Loft", 
        "Aria Assembly", "The Timbre Hall", "Virtuoso Venue", "The Velvet Resonance", "Echoes of Elysium", "Pure Tone Hall", 
        "The Unplugged Atrium", "Crystal Acoustic Wing", "The Hollow Oak Hall", 
        "Silent Stream Symphony", "The Natural Note", "Vibration Vault", 
        "The Pristine Chamber", "Acoustic Archway", "The Woodwind Well", 
        "Harmony Hollow", "The Sonorous Suite", "Clear Echo Hall"
    ],
    "Ballroom": [
        "The Gilded Coda", "Marcellus Grand Ballroom", "Crystal Floor Suites", 
        "The Royal Gala Hall", "Velvet Curtains Ballroom", "The chandelier Room", 
        "Moonlight Waltz Hall", "The Imperial Ballroom", "Satin Linens Hall", 
        "The Renaissance Suite", "Midnight Gala Ballroom", "The Polished Floor", 
        "Majestic Ballroom", "Heritage Hall", "The Grand Carousel Room"
    ],
    "Proscenium Theater": [
        "The Iron Mask Theater", "The Midnight Proscenium", "Curtain Call Commons", 
        "The Ghostlight Gallery", "Fable & Frame Theater", "The Silhouette Theater", 
        "Velvet Frame Playhouse", "The Dramatic Arch", "Grand Aperture Theater", 
        "The Golden Wing", "Masterpiece Stage", "The Red Drape Theater", 
        "Avenue Playhouse", "The Scenic Stage", "Legacy Proscenium"
    ],
    "Black Box Theater": [
        "The Vanguard Black Box", "Monologue Square", "The Indigo Stage", 
        "The Narrative Loft", "Void Stage Labs", "Dark Room Dramatics", 
        "The Minimalist Suite", "Blank Canvas Theater", "The Shadow Box", 
        "Inkwell Theater", "The Industrial Stage", "Underground Dramas", 
        "The Core Theater", "Primal Stage", "The Unseen Theater"
    ],
    "Thrust Stage Theater": [
        "The Three-Side Stage", "Proximity Playhouse", "The Intimate Angle", 
        "Vantage Point Theater", "The Peninsula Stage", "Surround Dramatics", 
        "The Forward Edge", "Convergence Theater", "The Bridge Stage", 
        "Actor’s Reach Theater", "The Engagement Suite", "Delta Stage", 
        "The Outpost Theater", "The Central Spoke", "Perspective Playhouse"
    ],
    "Performing Arts Center": [
        "Third Act Arts Center", "Beacon Arts Pavilion", "The Soliloquy Suite", 
        "Civic Muse Center", "The Heritage Arts Wing", "Unity Arts Complex", 
        "Metropolitan Muse", "The Cultural Spire", "Visionary Arts Center", 
        "The Creative Quarter", "Atlas Arts Pavilion", "Liberty Arts Hub", 
        "The Spectrum Center", "Foundation Arts Hall", "Pioneer Arts Center"
    ],
    "Grand Palace": [
        "The Sovereign Suite", "Imperial Majesty Hall", "The Regent’s Stage", 
        "Palace of the Muse", "The Royal Pavilion", "Crown Jewel Theater", 
        "Gilded Throne Hall", "The Noble Annex", "Dynasty Theater", 
        "High Court Arts", "The Aristocrat Stage", "Monarch’s Playhouse", 
        "The Citadel Palace", "Elysian Grandeur", "The Marble Monarch"
    ],
    "Opera House": [
        "The Obsidian Lyric House", "The Silverline Opera Annex", "Belladonna Opera House", 
        "The Meridian Aria", "Crestline Opera House", "The Diva’s Atrium", 
        "Gilded Rose Opera", "The Soprano Stage", "Tragedy & Triumph House", 
        "The Lyric Labyrinth", "Opus One House", "The Grand Libretto", 
        "Starlight Opera", "The Velvet Aria", "Aura Opera House"
    ],
    "Lyric Theater": [
        "The Melodic Stage", "Verse & Voice Theater", "The Lyric Loft", 
        "Harmonious House", "The Rhyme Theater", "Rhythmic Playhouse", 
        "The Songsmith Theater", "Vocal Vantage", "The Lyric Lane", 
        "Sonnet Stage", "Chorus House", "The Anthem Theater", 
        "Poetry in Motion Theater", "The Ballad Box", "Overture Theater"
    ],
    "Comedy Club": [
        "The Giggle Garrison", "Punchline Parlor", "Last Laugh Lounge", 
        "Chuckle & Chime", "The Irony Room", "Standup Central", 
        "The Roast Room", "Witticism Works", "The Guffaw Gallery", 
        "Banter Basement", "The Comedy Cask", "Laughter Loft", 
        "The Snicker Station", "Jester’s Junction", "The Daily Dose of Funny"
    ],
    "Boutique Theater": [
        "The Micro-Stage", "Velvet Seat Cinema", "The Artisan Theater", 
        "Curated Classics House", "The Niche Stage", "Elegance Theater", 
        "The Polished Playhouse", "Small Scale Cinema", "The Luxury Loft", 
        "Couture Theater", "The Refined Room", "Intimate Imagery", 
        "The Premiere Suite", "Elite Stage", "The Cinema Study"
    ],
    "Jazz Club": [
        "The Blue Note Basement", "The Satin Sax", "The Smoky Quaver", 
        "The Syncopated Cellar", "The Bebop Bistro", "Indigo Jazz Attic", 
        "The Brass Flamingo", "Rhythm & Rye", "The Low-End Lounge", 
        "Groove & Glass", "The Jazz Den", "Note-Worthy Nightclub", 
        "The Improvisation Lab", "Swing Street Station", "Cool Cat Club"
    ],
    "Intimate Lounge": [
        "The Velvet Vibe", "Whisper Lounge", "The Ember Room", 
        "Cozy Chord Corner", "The Midnight Parlor", "Mellow Moods Lounge", 
        "The Soft Note", "Twilight Lounge", "The Serene Suite", 
        "Quietude Lounge", "The Gentle Glow", "Subdued Sounds", 
        "The Lounge at Obsidian", "Soothe & Sip", "The Chill Chamber"
    ],
    "Big Top Tent": [
        "The Iron Ring Circus", "The Canvas Citadel", "The Spectacle Spire", 
        "Grand Stripe Pavilion", "The Sky-High Tent", "Acrobat Alley", 
        "The Ringmaster’s Reach", "Luminous Big Top", "The Aerial Annex", 
        "Golden Stake Circus", "The Traveling Titan", "Prism Pavilion", 
        "The High-Wire Hub", "Carousel Canvas", "Wonder-Wheel Tent"
    ],
    "Multipurpose Stadium": [
        "The Horizon Bowl", "The Gravity Dome", "Nebula Event Grounds", 
        "The Canvas Citadel", "Versatile Victory Field", "Adaptation Arena", 
        "The Transformer Stadium", "Flex-Field Arena", "The All-Phase Dome", 
        "Hybrid Horizon", "The Dynamic Arena", "Shift-Style Stadium", 
        "The Multi-Tiered Mound", "Spectrum Stadium", "The Omni-Venue"
    ]
}


OUTDOORS = [True, False]
PARKING = [True, False]
FOOD = [True, False]
ALCOHOL = [True, False]

REFERENCE_FIELDS = {
    "city": LOCATIONS,
    "neighborhood": NEIGHBORHOODS,
    "venue_types": VENUE_TYPES,
    "venue_names": VENUE_NAMES,
    "is_outdoors": OUTDOORS,
    "parking_available": PARKING,
    "serves_food": FOOD,
    "serves_alcohol": ALCOHOL,
}
