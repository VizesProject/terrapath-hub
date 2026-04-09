(function () {
  const eras = [
    { id: "prehardmode", label: { en: "Pre-Hardmode", ru: "До хардмода" } },
    { id: "hardmode", label: { en: "Hardmode", ru: "Хардмод" } },
    { id: "postmoonlord", label: { en: "Post-Moon Lord", ru: "После Мунлорда" } }
  ];

  const markers = [
    {
      id: "early-exploration",
      era: "prehardmode",
      icon: "assets/icons/terraria/items/cloud-in-a-bottle.png",
      title: { en: "Early exploration", ru: "Ранняя разведка" },
      description: {
        en: "Before stable bossing, while movement and chest routing still define most upgrades.",
        ru: "До стабильных боссов, когда прогресс в основном строится вокруг мобильности и поиска сундуков."
      }
    },
    {
      id: "pre-eye-of-cthulhu",
      era: "prehardmode",
      icon: "assets/icons/terraria/bosses/eye-of-cthulhu.png",
      title: { en: "Pre-Eye of Cthulhu", ru: "До Глаза Ктулху" },
      description: {
        en: "Arena setup, starter accessories, and first reliable damage options before the earliest boss check.",
        ru: "Подготовка арены, стартовых аксессуаров и первого надежного урона перед самым ранним босс-чеком."
      }
    },
    {
      id: "pre-skeletron",
      era: "prehardmode",
      icon: "assets/icons/terraria/items/enchanted-boomerang.png",
      title: { en: "Pre-Skeletron", ru: "До Скелетрона" },
      description: {
        en: "Dungeon access is still locked, so the guide should focus on surface and underground progression.",
        ru: "Данж еще закрыт, поэтому этап должен быть сфокусирован на наземной и подземной прогрессии."
      }
    },
    {
      id: "pre-wall-of-flesh",
      era: "prehardmode",
      icon: "assets/icons/terraria/items/iron-bar.png",
      title: { en: "Pre-Wall of Flesh", ru: "До Стены плоти" },
      description: {
        en: "Final pre-hardmode optimization before the world changes into hardmode.",
        ru: "Финальная доработка перед концом дохардмода и переходом мира в хардмод."
      }
    },
    {
      id: "hardmode-entry",
      era: "hardmode",
      icon: "assets/icons/terraria/ores/iron-ore.png",
      title: { en: "Hardmode entry", ru: "Старт хардмода" },
      description: {
        en: "Right after entering hardmode, when ore access, survival, and the first upgrades matter most.",
        ru: "Сразу после входа в хардмод, когда важнее всего новые руды, выживание и первые апгрейды."
      }
    },
    {
      id: "pre-mech",
      era: "hardmode",
      icon: "assets/icons/terraria/items/iron-bar.png",
      title: { en: "Pre-mech", ru: "До механиков" },
      description: {
        en: "Before the mechanical bosses, while the build is still stabilizing around hardmode crafting.",
        ru: "До механических боссов, когда билд еще собирается вокруг хардмодного крафта."
      }
    },
    {
      id: "post-mech",
      era: "hardmode",
      icon: "assets/icons/terraria/items/gold-broadsword.png",
      title: { en: "Post-mech", ru: "После механиков" },
      description: {
        en: "After all three mechanical bosses, with access to stronger crafting and clearer class direction.",
        ru: "После всех трех механических боссов, с доступом к более сильному крафту и четкой роли класса."
      }
    },
    {
      id: "pre-plantera",
      era: "hardmode",
      icon: "assets/icons/terraria/bosses/eye-of-cthulhu.png",
      title: { en: "Pre-Plantera", ru: "До Плантеры" },
      description: {
        en: "Jungle access and arena prep become the main bottlenecks for progression.",
        ru: "Главными ограничителями прогрессии становятся джунгли и подготовка арены."
      }
    },
    {
      id: "post-plantera",
      era: "hardmode",
      icon: "assets/icons/terraria/items/enchanted-boomerang.png",
      title: { en: "Post-Plantera", ru: "После Плантеры" },
      description: {
        en: "Dungeon, temple route planning, and specialty drops begin to shape the build.",
        ru: "Билд начинают определять данж, маршрут в храм и более узкие специализированные дропы."
      }
    },
    {
      id: "pre-golem",
      era: "hardmode",
      icon: "assets/icons/terraria/items/gold-broadsword.png",
      title: { en: "Pre-Golem", ru: "До Голема" },
      description: {
        en: "A short transition stage focused on temple access and preparing for the next boss gate.",
        ru: "Короткий переходный этап, завязанный на доступе в храм и подготовке к следующему босс-чеку."
      }
    },
    {
      id: "post-golem",
      era: "hardmode",
      icon: "assets/icons/terraria/items/iron-bar.png",
      title: { en: "Post-Golem", ru: "После Голема" },
      description: {
        en: "The build is mostly formed, and the guide can point players toward cultist or event preparation.",
        ru: "Билд уже почти собран, и этап может направлять игрока к культисту или ивентам."
      }
    },
    {
      id: "pre-cultist",
      era: "hardmode",
      icon: "assets/icons/terraria/items/cloud-in-a-bottle.png",
      title: { en: "Pre-Cultist", ru: "До Культиста" },
      description: {
        en: "A cleanup phase for last utility picks and polishing damage or survivability.",
        ru: "Этап доводки последних утилити-предметов и финальной полировки урона или выживаемости."
      }
    },
    {
      id: "pre-moon-lord",
      era: "hardmode",
      icon: "assets/icons/terraria/bosses/eye-of-cthulhu.png",
      title: { en: "Pre-Moon Lord", ru: "До Мунлорда" },
      description: {
        en: "The final pre-endgame setup where every slot should support the Moon Lord attempt directly.",
        ru: "Финальная подготовка перед эндгеймом, где каждый слот уже должен работать на битву с Мунлордом."
      }
    },
    {
      id: "post-moon-lord",
      era: "postmoonlord",
      icon: "assets/icons/terraria/items/gold-broadsword.png",
      title: { en: "Post-Moon Lord", ru: "После Мунлорда" },
      description: {
        en: "Endgame cleanup, final power spikes, and transition into full build completion.",
        ru: "Эндгейм-доработка, последние скачки силы и переход к полностью завершенному билду."
      }
    },
    {
      id: "endgame-farming",
      era: "postmoonlord",
      icon: "assets/icons/terraria/items/iron-bar.png",
      title: { en: "Endgame farming", ru: "Эндгейм-фарм" },
      description: {
        en: "Farming loops, event clears, and optimized equipment swaps become the main focus.",
        ru: "Основной фокус смещается на фарм, зачистку ивентов и оптимизированные перестановки экипировки."
      }
    },
    {
      id: "completionist-route",
      era: "postmoonlord",
      icon: "assets/icons/terraria/items/cloud-in-a-bottle.png",
      title: { en: "Completionist route", ru: "Маршрут для полного закрытия" },
      description: {
        en: "Use this for optional luxury upgrades, collections, or near-finished build paths.",
        ru: "Используйте это для роскошных опциональных апгрейдов, коллекций и почти завершенных путей сборки."
      }
    }
  ];

  function siteLanguage() {
    return window.terraPathSite?.getLanguage?.() === "ru" ? "ru" : "en";
  }

  function getEra(id) {
    return eras.find((era) => era.id === id) || null;
  }

  function getMarker(id) {
    return markers.find((marker) => marker.id === id) || null;
  }

  function eraLabel(id, language = siteLanguage()) {
    return getEra(id)?.label?.[language] || id;
  }

  function markerTitle(id, language = siteLanguage()) {
    return getMarker(id)?.title?.[language] || id;
  }

  function markerDescription(id, language = siteLanguage()) {
    return getMarker(id)?.description?.[language] || "";
  }

  function markersForEra(eraId) {
    return markers.filter((marker) => marker.era === eraId);
  }

  window.terraPathProgression = {
    eras,
    markers,
    getEra,
    getMarker,
    eraLabel,
    markerTitle,
    markerDescription,
    markersForEra
  };
})();
