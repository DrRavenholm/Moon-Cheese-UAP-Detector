# Third-party icon notices

This release uses selected **Font Awesome Free 6.7.2** SVG icons by Fonticons, Inc. (https://fontawesome.com/) for the About Moon Cheese page. The SVG artwork is served locally and retained unmodified; CSS adds the layout and background colours. Icons are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**: https://creativecommons.org/licenses/by/4.0/ . Full Font Awesome Free licensing details: https://fontawesome.com/license/free . Copyright © Fonticons, Inc. No Font Awesome webfonts or JavaScript library is bundled.

The website, services and social platform names/logos are the property of their respective owners. Links identify Dr Ravenholm's destinations; their presence does not imply affiliation, sponsorship or endorsement by the platforms.

## Astronomical data providers (downloaded separately by each installation)

The v1.0.1.2 Sky Maps downloader obtains astronomical data directly from third-party publicly accessible datasets **after** installation; these datasets are not bundled or redistributed in this source/release archive. The source names and URL for each file are shown in Sky Maps → Data & Updates.

- **D3-Celestial / Olaf Frohn and contributors:** star and constellation GeoJSON, star names and optional Messier/deep-sky catalogues: https://github.com/ofrohn/d3-celestial . Check that project's data attribution and applicable source licence when reusing derived catalogues.
- **NASA/JPL NAIF:** planetary ephemeris DE440s SPK, https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp . Trajectory and time predictions are computational estimates.
- **CelesTrak:** GP/OMM active-satellite orbital data, https://celestrak.org/NORAD/elements/ . Respect https://celestrak.org/usage-policy.php and retained orbital epochs; orbital data may become outdated. Satellite categories and their operators retain their respective designations.
- **Natural Earth:** public-domain world outlines, https://www.naturalearthdata.com/ .
- **Skyfield** / Brandon Rhodes and contributors: astronomy and satellite-propagation calculations supplied separately through Raspberry Pi OS/Debian packages, https://rhodesmill.org/skyfield/ .

Moon Cheese does not imply endorsement by any of these providers. No paid API or developer key is required for the listed astronomy sources. Future source availability, terms and formats can change.
