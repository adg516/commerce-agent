from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CATALOGS_DIR = DATA_DIR / "catalogs"


def make_product(
    *,
    product_id: str,
    name: str,
    brand: str,
    category: str,
    subcategory: str,
    description: str,
    price: float,
    activity: list[str],
    fit: str,
    material: str,
    color: str,
    season: list[str],
    tags: list[str],
    image_path: str,
) -> dict:
    return {
        "id": product_id,
        "name": name,
        "brand": brand,
        "category": category,
        "subcategory": subcategory,
        "description": description,
        "price": round(price, 2),
        "gender": "unisex",
        "activity": activity,
        "fit": fit,
        "material": material,
        "color": color,
        "season": season,
        "tags": tags,
        "image_path": image_path,
        "reviews": [
            {"text": "Solid quality for the price and easy to use day-to-day.", "rating": 4},
            {"text": "Looks great and performs as expected.", "rating": 5},
        ],
    }


def electronics_catalog() -> list[dict]:
    rows = [
        ("Nimbus Pro Laptop 14", "CircuitOne", "computers", "laptops", "Compact 14-inch laptop tuned for productivity and travel.", 1299, ["work", "travel"], "portable", "aluminum", "silver", ["all"], ["lightweight", "battery-life"], "/static/images/footwear.png"),
        ("AeroBook Lite 13", "VoltEdge", "computers", "laptops", "Everyday ultrabook with efficient performance for students and remote teams.", 899, ["work", "study"], "portable", "aluminum", "space gray", ["all"], ["everyday", "portable"], "/static/images/footwear.png"),
        ("PixelPulse Phone X", "NovaMobile", "phones", "smartphones", "Flagship smartphone with bright display and fast camera pipeline.", 999, ["daily", "travel"], "slim", "glass aluminum", "black", ["all"], ["camera", "premium"], "/static/images/accessories.png"),
        ("PixelPulse Phone SE", "NovaMobile", "phones", "smartphones", "Value-focused smartphone with all-day battery and clean software.", 549, ["daily"], "slim", "aluminum", "blue", ["all"], ["value", "battery"], "/static/images/accessories.png"),
        ("EchoWave ANC Headphones", "SoundArc", "audio", "headphones", "Over-ear ANC headphones for commuting and focused work.", 249, ["commute", "work"], "over-ear", "composite", "black", ["all"], ["anc", "wireless"], "/static/images/accessories.png"),
        ("EchoWave Mini Buds", "SoundArc", "audio", "earbuds", "Pocketable earbuds with clear calls and stable Bluetooth pairing.", 119, ["daily", "gym"], "in-ear", "polycarbonate", "white", ["all"], ["wireless", "calls"], "/static/images/accessories.png"),
        ("FrameCast 4K Monitor", "DisplayLab", "displays", "monitors", "27-inch 4K IPS monitor for editing, analysis, and creative workflows.", 429, ["work", "creative"], "desk", "metal plastic", "black", ["all"], ["4k", "ips"], "/static/images/outerwear.png"),
        ("HyperDock 9-in-1", "DockForge", "accessories", "docks", "USB-C docking hub with HDMI, Ethernet, SD, and power passthrough.", 99, ["work"], "compact", "aluminum", "gray", ["all"], ["usb-c", "hub"], "/static/images/accessories.png"),
        ("PulseWatch Fit", "BodySync", "wearables", "smartwatches", "Fitness smartwatch with GPS tracking and recovery insights.", 279, ["fitness", "running"], "wrist", "polymer", "black", ["all"], ["gps", "health"], "/static/images/accessories.png"),
        ("TrailCam Action 2", "MotionPeak", "cameras", "action-cameras", "Rugged 4K action camera with stabilization for outdoor adventures.", 329, ["travel", "outdoor"], "compact", "polycarbonate", "black", ["all"], ["4k", "rugged"], "/static/images/outerwear.png"),
        ("SkyMesh WiFi Router", "NetOrbit", "networking", "routers", "WiFi 6 mesh-ready router built for low-latency home coverage.", 189, ["home"], "desktop", "plastic", "white", ["all"], ["wifi6", "mesh"], "/static/images/accessories.png"),
        ("CorePad Mechanical Keyboard", "TypeCraft", "accessories", "keyboards", "Mechanical keyboard with tactile switches and hot-swap support.", 139, ["work", "gaming"], "desk", "aluminum", "black", ["all"], ["mechanical", "rgb"], "/static/images/accessories.png"),
        ("SwiftGlide Mouse Pro", "TypeCraft", "accessories", "mice", "Ergonomic wireless mouse with high-precision sensor and USB-C charging.", 79, ["work"], "ergonomic", "polymer", "graphite", ["all"], ["wireless", "ergonomic"], "/static/images/accessories.png"),
        ("ChargeBrick 100W", "VoltEdge", "accessories", "chargers", "Dual USB-C 100W GaN charger for laptop and phone fast-charging.", 69, ["travel"], "compact", "composite", "white", ["all"], ["gan", "fast-charge"], "/static/images/accessories.png"),
        ("StudioMic USB", "WaveForm", "audio", "microphones", "Plug-and-play condenser USB mic for streaming and online calls.", 149, ["work", "streaming"], "desk", "metal", "black", ["all"], ["usb", "creator"], "/static/images/accessories.png"),
        ("VisionPanel 34", "DisplayLab", "displays", "ultrawide-monitors", "34-inch ultrawide monitor designed for multitasking and dashboards.", 599, ["work", "creative"], "desk", "metal plastic", "black", ["all"], ["ultrawide", "productivity"], "/static/images/outerwear.png"),
        ("SnapLite Tablet 11", "CircuitOne", "tablets", "tablets", "11-inch tablet for notes, drawing, and media on the go.", 499, ["study", "travel"], "portable", "aluminum", "gray", ["all"], ["tablet", "portable"], "/static/images/accessories.png"),
        ("RenderBox Mini PC", "VoltEdge", "computers", "mini-pcs", "Small-form desktop with strong thermals for coding and media tasks.", 749, ["work", "home"], "desktop", "aluminum", "black", ["all"], ["compact", "desktop"], "/static/images/footwear.png"),
        ("DataVault SSD 2TB", "CoreStore", "storage", "portable-ssd", "Fast portable SSD with hardware encryption and USB-C interface.", 219, ["work", "travel"], "portable", "aluminum", "blue", ["all"], ["ssd", "encrypted"], "/static/images/accessories.png"),
        ("BeamCast Projector Go", "LightFrame", "displays", "projectors", "Portable smart projector for movie nights and presentations.", 459, ["home", "travel"], "portable", "polycarbonate", "white", ["all"], ["portable", "smart"], "/static/images/outerwear.png"),
    ]
    products: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        products.append(
            make_product(
                product_id=f"elec_{idx:03d}",
                name=row[0],
                brand=row[1],
                category=row[2],
                subcategory=row[3],
                description=row[4],
                price=row[5],
                activity=row[6],
                fit=row[7],
                material=row[8],
                color=row[9],
                season=row[10],
                tags=row[11],
                image_path=row[12],
            )
        )
    return products


def home_catalog() -> list[dict]:
    rows = [
        ("Oakline Dining Set", "HearthCo", "furniture", "dining", "Modern 4-seat dining set with durable finish and easy-clean surface.", 699, ["dining", "home"], "regular", "oak wood", "walnut", ["all"], ["family", "durable"], "/static/images/outerwear.png"),
        ("CloudRest Sofa 3-Seater", "NestForm", "furniture", "sofas", "Comfort-first sofa with deep cushions and stain-resistant weave.", 1099, ["lounging", "home"], "regular", "performance fabric", "sand", ["all"], ["comfort", "living-room"], "/static/images/outerwear.png"),
        ("ChefCore Pan Set", "CookSmith", "cookware", "pan-sets", "Non-stick cookware set with induction compatibility.", 189, ["cooking"], "regular", "hard-anodized aluminum", "black", ["all"], ["non-stick", "induction"], "/static/images/accessories.png"),
        ("PureBrew Kettle", "CookSmith", "appliances", "kettles", "Electric gooseneck kettle with precise temperature presets.", 89, ["coffee", "tea"], "compact", "stainless steel", "matte black", ["all"], ["precision", "electric"], "/static/images/accessories.png"),
        ("FreshKeep Container Kit", "PantryPro", "storage", "food-storage", "Airtight stackable food containers for pantry organization.", 49, ["organizing"], "regular", "bpa-free plastic", "clear", ["all"], ["airtight", "stackable"], "/static/images/accessories.png"),
        ("LumenGlow Floor Lamp", "BrightNest", "lighting", "floor-lamps", "Dimmable floor lamp with warm-to-cool light modes.", 129, ["home", "reading"], "regular", "steel", "white", ["all"], ["dimmable", "ambient"], "/static/images/outerwear.png"),
        ("SleepEase Memory Pillow", "Restory", "bedding", "pillows", "Contour memory foam pillow for neck alignment.", 69, ["sleep"], "regular", "memory foam", "white", ["all"], ["ergonomic", "sleep"], "/static/images/accessories.png"),
        ("AromaMist Diffuser", "ZenAura", "decor", "diffusers", "Ultrasonic aroma diffuser with quiet operation and timer modes.", 39, ["relaxation"], "compact", "polypropylene", "stone", ["all"], ["quiet", "relax"], "/static/images/accessories.png"),
        ("GraniteServe Dinnerware", "HearthCo", "dining", "dinnerware", "16-piece stoneware dinner set for everyday meals.", 99, ["dining"], "regular", "stoneware", "slate", ["all"], ["dishwasher-safe", "set"], "/static/images/accessories.png"),
        ("SmartSteam Iron", "HomePulse", "appliances", "irons", "Steam iron with anti-drip and auto shut-off.", 59, ["laundry"], "compact", "ceramic steel", "blue", ["all"], ["steam", "safe"], "/static/images/accessories.png"),
        ("FoldMate Laundry Rack", "HomePulse", "laundry", "drying-racks", "Space-saving foldable drying rack for indoor use.", 44, ["laundry"], "regular", "steel", "silver", ["all"], ["foldable", "space-saving"], "/static/images/outerwear.png"),
        ("CedarStack Shelf Unit", "NestForm", "furniture", "shelving", "Open shelf unit for books, plants, and office storage.", 179, ["organizing"], "regular", "cedar wood", "natural", ["all"], ["storage", "display"], "/static/images/outerwear.png"),
        ("QuietBlend Blender", "CookSmith", "appliances", "blenders", "High-speed blender with low-noise housing and pulse mode.", 149, ["cooking"], "regular", "tritan steel", "black", ["all"], ["quiet", "smoothies"], "/static/images/accessories.png"),
        ("AirPure HEPA 300", "BreatheWell", "appliances", "air-purifiers", "HEPA purifier designed for medium rooms and allergy relief.", 229, ["home"], "regular", "composite", "white", ["all"], ["hepa", "allergy"], "/static/images/accessories.png"),
        ("CrispCotton Sheet Set", "Restory", "bedding", "sheet-sets", "Breathable cotton sateen sheet set with deep pockets.", 89, ["sleep"], "regular", "cotton", "sage", ["all"], ["breathable", "soft"], "/static/images/accessories.png"),
        ("StoneBoard Cutting Set", "CookSmith", "kitchen-tools", "cutting-boards", "Three-piece anti-slip cutting board set for meal prep.", 39, ["cooking"], "regular", "composite", "charcoal", ["all"], ["prep", "durable"], "/static/images/accessories.png"),
        ("EntryEase Shoe Bench", "HearthCo", "furniture", "entryway", "Bench with hidden shoe storage for clean entryways.", 159, ["organizing"], "regular", "engineered wood", "oak", ["all"], ["entryway", "storage"], "/static/images/outerwear.png"),
        ("GlowFrame Wall Mirror", "BrightNest", "decor", "mirrors", "Large wall mirror to brighten and open up spaces.", 119, ["decor"], "regular", "glass steel", "black", ["all"], ["decor", "light"], "/static/images/outerwear.png"),
        ("MealPrep Glass Boxes", "PantryPro", "storage", "meal-prep", "Glass containers with locking lids for weekly meal prep.", 59, ["organizing", "cooking"], "regular", "borosilicate glass", "clear", ["all"], ["meal-prep", "microwave-safe"], "/static/images/accessories.png"),
        ("NestHeat Throw Blanket", "Restory", "bedding", "throws", "Ultra-soft throw blanket for couches and reading nooks.", 49, ["lounging"], "regular", "microfiber", "dusty rose", ["fall", "winter"], ["cozy", "soft"], "/static/images/accessories.png"),
    ]
    products: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        products.append(
            make_product(
                product_id=f"home_{idx:03d}",
                name=row[0],
                brand=row[1],
                category=row[2],
                subcategory=row[3],
                description=row[4],
                price=row[5],
                activity=row[6],
                fit=row[7],
                material=row[8],
                color=row[9],
                season=row[10],
                tags=row[11],
                image_path=row[12],
            )
        )
    return products


def outdoor_catalog() -> list[dict]:
    rows = [
        ("SummitLite Tent 2P", "AeroTrail", "shelter", "tents", "Two-person lightweight backpacking tent with quick-pitch frame.", 289, ["camping", "hiking"], "regular", "ripstop nylon", "forest green", ["spring", "summer", "fall"], ["lightweight", "backpacking"], "/static/images/outerwear.png"),
        ("RidgeCamp Tent 4P", "NorthArc", "shelter", "tents", "Spacious family camping tent with weather-ready fly.", 369, ["camping"], "regular", "polyester", "sand", ["spring", "summer", "fall"], ["family", "weather-resistant"], "/static/images/outerwear.png"),
        ("TrailFlow Backpack 35L", "AeroTrail", "packs", "backpacks", "Versatile day-hike pack with ventilated back panel.", 139, ["hiking", "travel"], "regular", "recycled nylon", "black", ["all"], ["ventilated", "daypack"], "/static/images/bottoms.png"),
        ("AlpineHaul Pack 60L", "NorthArc", "packs", "backpacks", "Long-haul trekking backpack with adjustable frame.", 229, ["hiking", "camping"], "regular", "ripstop nylon", "charcoal", ["all"], ["trekking", "load-support"], "/static/images/bottoms.png"),
        ("HeatCore Sleeping Bag", "CampForge", "sleep", "sleeping-bags", "Three-season sleeping bag with synthetic insulation.", 159, ["camping"], "regular", "polyester fill", "blue", ["spring", "summer", "fall"], ["3-season", "warm"], "/static/images/accessories.png"),
        ("FrostGuard Sleeping Bag", "CampForge", "sleep", "sleeping-bags", "Cold-weather sleeping bag rated for winter nights.", 229, ["camping"], "regular", "down blend", "navy", ["winter"], ["winter", "insulated"], "/static/images/accessories.png"),
        ("PeakFlame Stove", "WildCook", "camp-kitchen", "stoves", "Compact camp stove with stable burner and fast boil.", 79, ["camping"], "compact", "steel", "gray", ["all"], ["portable", "fast-boil"], "/static/images/accessories.png"),
        ("SummitCook Pot Set", "WildCook", "camp-kitchen", "cookware", "Nestable camp cookware set for trail meals.", 69, ["camping"], "compact", "anodized aluminum", "silver", ["all"], ["nestable", "lightweight"], "/static/images/accessories.png"),
        ("GraniteGrip Trek Poles", "AeroTrail", "hiking-gear", "trekking-poles", "Adjustable trekking poles for stability on climbs.", 89, ["hiking"], "regular", "carbon aluminum", "black", ["all"], ["stability", "adjustable"], "/static/images/accessories.png"),
        ("RiverTrail Sandals", "StridePeak", "footwear", "sandals", "Quick-dry outdoor sandals with textured grip.", 74, ["hiking", "travel"], "regular", "synthetic rubber", "olive", ["summer"], ["quick-dry", "grip"], "/static/images/footwear.png"),
        ("RockLine Approach Shoe", "StridePeak", "footwear", "approach-shoes", "Low-profile shoe with sticky outsole for rocky trails.", 124, ["hiking", "climbing"], "regular", "mesh suede", "graphite", ["all"], ["traction", "approach"], "/static/images/footwear.png"),
        ("StormShell Rain Jacket", "NorthArc", "outerwear", "rain-jackets", "Packable waterproof shell for sudden weather changes.", 149, ["hiking", "travel"], "regular", "laminated nylon", "teal", ["spring", "fall"], ["waterproof", "packable"], "/static/images/outerwear.png"),
        ("CanyonSun Hat", "AeroTrail", "accessories", "hats", "Wide-brim sun hat with breathable mesh vents.", 34, ["hiking", "travel"], "regular", "nylon", "sand", ["summer"], ["sun-protection", "breathable"], "/static/images/accessories.png"),
        ("TrailHydro Flask 1L", "CampForge", "hydration", "bottles", "Insulated bottle that keeps drinks cold on long hikes.", 39, ["hiking", "camping"], "regular", "stainless steel", "blue", ["all"], ["insulated", "durable"], "/static/images/accessories.png"),
        ("NightBeam Headlamp", "NorthArc", "lighting", "headlamps", "Rechargeable headlamp with flood and spotlight modes.", 49, ["camping", "hiking"], "compact", "polymer", "black", ["all"], ["rechargeable", "night-hike"], "/static/images/accessories.png"),
        ("CampRest Sleeping Pad", "CampForge", "sleep", "sleeping-pads", "Inflatable sleeping pad with compact packed size.", 99, ["camping"], "regular", "ripstop nylon", "orange", ["all"], ["inflatable", "compact"], "/static/images/accessories.png"),
        ("BoulderGrip Gloves", "AeroTrail", "accessories", "gloves", "Durable gloves for rope handling and chilly mornings.", 29, ["climbing", "hiking"], "fitted", "synthetic leather", "black", ["fall", "winter"], ["grip", "durable"], "/static/images/accessories.png"),
        ("TrailMap GPS Beacon", "NorthArc", "navigation", "gps", "Compact emergency beacon with GPS tracking and SOS.", 199, ["hiking", "camping"], "compact", "polycarbonate", "orange", ["all"], ["safety", "gps"], "/static/images/accessories.png"),
        ("SummitChair Foldable", "CampForge", "camp-furniture", "chairs", "Lightweight foldable camping chair with cup holder.", 59, ["camping"], "regular", "aluminum fabric", "forest", ["all"], ["foldable", "comfort"], "/static/images/outerwear.png"),
        ("BaseCamp Table Lite", "CampForge", "camp-furniture", "tables", "Portable camping table with quick setup legs.", 79, ["camping"], "regular", "aluminum", "silver", ["all"], ["portable", "quick-setup"], "/static/images/outerwear.png"),
    ]
    products: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        products.append(
            make_product(
                product_id=f"out_{idx:03d}",
                name=row[0],
                brand=row[1],
                category=row[2],
                subcategory=row[3],
                description=row[4],
                price=row[5],
                activity=row[6],
                fit=row[7],
                material=row[8],
                color=row[9],
                season=row[10],
                tags=row[11],
                image_path=row[12],
            )
        )
    return products


def streetwear_catalog() -> list[dict]:
    rows = [
        ("MetroPulse Hoodie", "VoltWeave", "tops", "hoodies", "Relaxed heavyweight hoodie with clean street-ready silhouette.", 72, ["casual", "streetwear"], "oversized", "cotton fleece", "black", ["fall", "winter"], ["street", "cozy"], "/static/images/tops.png"),
        ("Skyline Crop Hoodie", "VoltWeave", "tops", "hoodies", "Cropped hoodie with soft brushed interior for layered fits.", 64, ["casual"], "cropped", "cotton blend", "sage", ["spring", "fall"], ["cropped", "layering"], "/static/images/tops.png"),
        ("Nightline Cargo Pant", "CoreMotion", "bottoms", "cargo-pants", "Utility cargo pants with tapered leg and stretch waist.", 78, ["casual", "travel"], "regular", "cotton twill", "charcoal", ["all"], ["utility", "street"], "/static/images/bottoms.png"),
        ("StrideSplit Run Shorts", "SprintFlex", "bottoms", "shorts", "Split-hem shorts with mesh liner and zip pocket.", 38, ["running", "training"], "regular", "polyester", "teal", ["spring", "summer"], ["lightweight", "zip-pocket"], "/static/images/bottoms.png"),
        ("BlockTone Tee", "PeakForm", "tops", "t-shirts", "Boxy tee with premium drape for clean street styling.", 36, ["casual"], "boxy", "cotton", "off-white", ["all"], ["boxy", "minimal"], "/static/images/tops.png"),
        ("CityWave Overshirt", "NorthArc", "outerwear", "overshirts", "Midweight overshirt for transitional weather layering.", 84, ["casual", "travel"], "regular", "cotton blend", "olive", ["spring", "fall"], ["layering", "transitional"], "/static/images/outerwear.png"),
        ("ArcRunner Retro", "SprintFlex", "footwear", "sneakers", "Retro runner silhouette with cushioned daily comfort.", 109, ["casual", "walking"], "regular", "mesh suede", "navy", ["all"], ["retro", "daily"], "/static/images/footwear.png"),
        ("LunaCourt Classic", "CoreMotion", "footwear", "sneakers", "Court-inspired sneaker with clean lines and stable base.", 99, ["casual"], "regular", "synthetic leather", "white", ["all"], ["classic", "court"], "/static/images/footwear.png"),
        ("Signal Beanie", "AeroTrail", "accessories", "beanies", "Rib-knit beanie for cold days and city walks.", 24, ["casual"], "regular", "acrylic wool", "black", ["fall", "winter"], ["warm", "street"], "/static/images/accessories.png"),
        ("CrossCity Sling", "VoltWeave", "accessories", "bags", "Compact sling bag with internal organizer pockets.", 42, ["travel", "casual"], "compact", "recycled nylon", "graphite", ["all"], ["edc", "compact"], "/static/images/accessories.png"),
        ("RiverStone Denim Jogger", "PeakForm", "bottoms", "joggers", "Jogger fit with denim look and stretch comfort.", 68, ["casual"], "tapered", "denim stretch", "indigo", ["all"], ["jogger", "denim-look"], "/static/images/bottoms.png"),
        ("NeonTrim Windbreaker", "SprintFlex", "outerwear", "windbreakers", "Lightweight windbreaker with contrast trim and hood.", 79, ["casual", "running"], "regular", "nylon", "black neon", ["spring", "fall"], ["wind", "lightweight"], "/static/images/outerwear.png"),
        ("MonoTone Track Jacket", "CoreMotion", "outerwear", "track-jackets", "Streamlined track jacket with subtle matte finish.", 74, ["casual", "training"], "regular", "poly tricot", "stone", ["spring", "fall"], ["track", "minimal"], "/static/images/outerwear.png"),
        ("Gridline Tee Long", "NorthArc", "tops", "long-sleeves", "Long-sleeve tee with breathable cotton and relaxed drape.", 44, ["casual"], "regular", "cotton", "dusty rose", ["all"], ["long-sleeve", "soft"], "/static/images/tops.png"),
        ("FlexCourt Shorts", "PeakForm", "bottoms", "shorts", "Athletic shorts that pair with tees and hoodies for city wear.", 41, ["casual", "training"], "regular", "poly blend", "sand", ["summer"], ["versatile", "athleisure"], "/static/images/bottoms.png"),
        ("MetroStep Knit Sneaker", "VoltWeave", "footwear", "sneakers", "Breathable knit sneaker for all-day city movement.", 114, ["walking", "casual"], "regular", "knit mesh", "gray", ["all"], ["knit", "all-day"], "/static/images/footwear.png"),
        ("SignalChain Necklace", "AeroTrail", "accessories", "jewelry", "Minimal stainless necklace for subtle styling.", 29, ["casual"], "regular", "stainless steel", "silver", ["all"], ["minimal", "accessory"], "/static/images/accessories.png"),
        ("PatchLogo Crew", "CoreMotion", "tops", "sweatshirts", "Classic crewneck sweatshirt with understated chest patch.", 58, ["casual"], "regular", "cotton fleece", "heather gray", ["fall", "winter"], ["crewneck", "everyday"], "/static/images/tops.png"),
        ("Nomad Utility Vest", "NorthArc", "outerwear", "vests", "Layering vest with utility pockets and matte finish.", 69, ["casual", "travel"], "regular", "nylon", "olive", ["spring", "fall"], ["utility", "layering"], "/static/images/outerwear.png"),
        ("StreetStride Cap", "PeakForm", "accessories", "caps", "Low-profile cap with moisture-wicking inner band.", 26, ["casual"], "regular", "cotton nylon", "navy", ["spring", "summer"], ["cap", "daily"], "/static/images/accessories.png"),
    ]
    products: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        products.append(
            make_product(
                product_id=f"str_{idx:03d}",
                name=row[0],
                brand=row[1],
                category=row[2],
                subcategory=row[3],
                description=row[4],
                price=row[5],
                activity=row[6],
                fit=row[7],
                material=row[8],
                color=row[9],
                season=row[10],
                tags=row[11],
                image_path=row[12],
            )
        )
    return products


def beauty_catalog() -> list[dict]:
    rows = [
        ("HydraCalm Gel Cleanser", "DermaBloom", "skincare", "cleansers", "Gentle gel cleanser that removes oil without stripping the skin.", 24, ["daily", "skincare"], "regular", "gel formula", "clear", ["all"], ["gentle", "daily"], "/static/images/accessories.png"),
        ("Vitamin C Bright Serum", "DermaBloom", "skincare", "serums", "Brightening serum that targets dullness and uneven tone.", 38, ["daily", "skincare"], "regular", "serum", "amber", ["all"], ["brightening", "antioxidant"], "/static/images/accessories.png"),
        ("Barrier Repair Cream", "PureLeaf", "skincare", "moisturizers", "Rich moisturizer designed to support skin barrier recovery.", 32, ["daily", "night"], "regular", "cream", "white", ["all"], ["hydrating", "barrier"], "/static/images/accessories.png"),
        ("SPF 50 Mineral Shield", "PureLeaf", "skincare", "sunscreen", "Mineral sunscreen with broad-spectrum UV protection.", 29, ["daily", "outdoor"], "regular", "mineral lotion", "ivory", ["all"], ["spf50", "uv-protection"], "/static/images/accessories.png"),
        ("CloudTint Skin Tint", "LumaHue", "makeup", "skin-tints", "Light coverage skin tint with breathable finish.", 34, ["daily", "makeup"], "regular", "liquid tint", "neutral", ["all"], ["light-coverage", "natural"], "/static/images/accessories.png"),
        ("SoftBlend Concealer", "LumaHue", "makeup", "concealers", "Buildable concealer for brightening and spot correction.", 22, ["daily", "makeup"], "regular", "liquid", "beige", ["all"], ["buildable", "blendable"], "/static/images/accessories.png"),
        ("VelvetMatte Lip Color", "StudioGlow", "makeup", "lips", "Comfort matte lip color with long wear and soft feel.", 19, ["daily", "night"], "regular", "cream matte", "rose", ["all"], ["long-wear", "matte"], "/static/images/accessories.png"),
        ("LashLift Mascara", "StudioGlow", "makeup", "eyes", "Lengthening mascara with smudge-resistant formula.", 21, ["daily", "makeup"], "regular", "mascara", "black", ["all"], ["lengthening", "smudge-resistant"], "/static/images/accessories.png"),
        ("GlossLock Brow Gel", "LumaHue", "makeup", "brows", "Clear brow gel to set and shape with flexible hold.", 16, ["daily", "makeup"], "regular", "gel", "clear", ["all"], ["brows", "hold"], "/static/images/accessories.png"),
        ("SilkRepair Shampoo", "RootLab", "haircare", "shampoo", "Sulfate-free shampoo for shine and gentle cleansing.", 27, ["haircare"], "regular", "liquid", "clear", ["all"], ["sulfate-free", "shine"], "/static/images/accessories.png"),
        ("SilkRepair Conditioner", "RootLab", "haircare", "conditioner", "Lightweight conditioner to smooth and detangle.", 27, ["haircare"], "regular", "cream", "white", ["all"], ["detangle", "smooth"], "/static/images/accessories.png"),
        ("Scalp Reset Scrub", "RootLab", "haircare", "scalp-treatments", "Exfoliating scalp scrub for weekly buildup reset.", 29, ["haircare"], "regular", "scrub", "mint", ["all"], ["scalp-care", "weekly"], "/static/images/accessories.png"),
        ("Overnight Renewal Mask", "DermaBloom", "skincare", "masks", "Hydrating overnight mask for softer morning skin.", 36, ["night", "skincare"], "regular", "gel-cream", "lavender", ["all"], ["overnight", "hydrating"], "/static/images/accessories.png"),
        ("CalmMist Toner", "PureLeaf", "skincare", "toners", "Alcohol-free toner that soothes and preps skin.", 23, ["daily", "skincare"], "regular", "water-based", "clear", ["all"], ["soothing", "prep"], "/static/images/accessories.png"),
        ("Daily Glow Exfoliant", "DermaBloom", "skincare", "exfoliants", "Mild chemical exfoliant for smoother texture.", 31, ["night", "skincare"], "regular", "liquid", "clear", ["all"], ["texture", "gentle-acid"], "/static/images/accessories.png"),
        ("AirTouch Dry Shampoo", "RootLab", "haircare", "dry-shampoo", "Oil-absorbing dry shampoo with invisible finish.", 21, ["haircare", "travel"], "regular", "powder spray", "white", ["all"], ["refresh", "no-residue"], "/static/images/accessories.png"),
        ("Precision Blend Sponge", "StudioGlow", "tools", "sponges", "Soft makeup sponge for seamless liquid blending.", 12, ["makeup"], "regular", "foam", "pink", ["all"], ["blend", "tool"], "/static/images/accessories.png"),
        ("ProDetail Brush Set", "StudioGlow", "tools", "brush-sets", "Five-piece brush set for base, eyes, and detail work.", 42, ["makeup"], "regular", "synthetic fibers", "black", ["all"], ["brushes", "set"], "/static/images/accessories.png"),
        ("Travel Ritual Kit", "PureLeaf", "sets", "travel-kits", "TSA-friendly skincare set for weekend trips.", 39, ["travel", "skincare"], "compact", "mixed", "multi", ["all"], ["travel", "kit"], "/static/images/accessories.png"),
        ("Night Repair Eye Cream", "DermaBloom", "skincare", "eye-care", "Peptide-rich eye cream for overnight hydration.", 35, ["night", "skincare"], "regular", "cream", "ivory", ["all"], ["peptides", "hydration"], "/static/images/accessories.png"),
    ]
    products: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        products.append(
            make_product(
                product_id=f"bea_{idx:03d}",
                name=row[0],
                brand=row[1],
                category=row[2],
                subcategory=row[3],
                description=row[4],
                price=row[5],
                activity=row[6],
                fit=row[7],
                material=row[8],
                color=row[9],
                season=row[10],
                tags=row[11],
                image_path=row[12],
            )
        )
    return products


def write_catalog(slug: str, products: list[dict]) -> None:
    target_dir = CATALOGS_DIR / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "catalog.json").write_text(json.dumps(products, indent=2), encoding="utf-8")


def main() -> None:
    CATALOGS_DIR.mkdir(parents=True, exist_ok=True)
    (CATALOGS_DIR / "_uploads").mkdir(parents=True, exist_ok=True)

    legacy_catalog_path = DATA_DIR / "catalog.json"
    if legacy_catalog_path.exists():
        athletic_dir = CATALOGS_DIR / "athletic"
        athletic_dir.mkdir(parents=True, exist_ok=True)
        athletic_json = athletic_dir / "catalog.json"
        athletic_json.write_text(legacy_catalog_path.read_text(encoding="utf-8"), encoding="utf-8")
        legacy_embeddings = DATA_DIR / "embeddings.npy"
        if legacy_embeddings.exists():
            (athletic_dir / "embeddings.npy").write_bytes(legacy_embeddings.read_bytes())

    write_catalog("electronics", electronics_catalog())
    write_catalog("home", home_catalog())
    write_catalog("outdoor", outdoor_catalog())
    write_catalog("streetwear", streetwear_catalog())
    write_catalog("beauty", beauty_catalog())

    print("Generated catalogs under data/catalogs/")


if __name__ == "__main__":
    main()
