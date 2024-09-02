maptilersdk.config.apiKey = MAP_TILER_API_KEY;

// get lat and lng parmeter from url
const urlParams = new URLSearchParams(window.location.search);
const latParam = parseFloat(urlParams.get("lat"));
const lngParam = parseFloat(urlParams.get("lng"));
const zoomParam = parseInt(urlParams.get("zoom"));
// test if lat is NaN
let initialCenter = [37, -7.669];
let initialZoom = 5;
if (!isNaN(latParam) && !isNaN(lngParam)) {
  initialCenter = [lngParam, latParam];
}
if (!isNaN(zoomParam)) {
  initialZoom = zoomParam;
}

const map = new maptilersdk.Map({
  container: "map",
  style: maptilersdk.MapStyle.OUTDOOR,
  center: initialCenter,
  zoom: initialZoom,
});
map.on("load", async function () {
  map.addSource("photos", { type: "geojson", data: "photos.json" });

  const icons = {
    lodging: await map.loadImage("icons/lodging.png"),
    airport: await map.loadImage("icons/airport.png"),
    point_of_interest: await map.loadImage("icons/point_of_interest.png"),
    photo: await map.loadImage("icons/photo.png"),
  };
  for (let icon in icons) {
    // replace default versions of icons
    if (map.hasImage(icon)) map.removeImage(icon);
    map.addImage(icon, icons[icon].data);
  }
  // show photos at zoom level 8 and above
  map.addLayer({
    id: "photos",
    minzoom: 8,
    type: "symbol",
    source: "photos",
    filter: ["all", ["==", "$type", "Point"], ["==", "icon", "photo"]],
    layout: {
      "icon-image": ["get", "icon"],
    },
  });
  // show non-photo points at all zoom levels
  map.addLayer({
    id: "points",
    type: "symbol",
    source: "photos",
    filter: ["all", ["==", "$type", "Point"], ["!=", "icon", "photo"]],
    layout: {
      "icon-image": ["get", "icon"],
    },
  });
  // add line feature for driving route
  /*
  map.addLayer({
    id: "route",
    type: "line",
    source: "photos",
    layout: {},
    paint: {
      "line-color": "rgb(68, 138, 255)",
      "line-width": 2,
    },
  });
  */

  const popup = new maptilersdk.Popup({
    closeButton: false,
    closeOnClick: false,
  });

  function showPopup(e) {
    // from https://docs.maptiler.com/sdk-js/examples/popup-on-hover/
    // Change the cursor style as a UI indicator.
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features[0];
    const coordinates = feature.geometry.coordinates.slice();
    let description = "";
    if (feature.properties.description !== undefined) {
      description = feature.properties.description;
    }
    if (feature.properties.name !== undefined) {
      description = feature.properties.name;
    }
    if (feature.properties.image !== undefined) {
      description = `<div class="card">
        <img class="card-img-top" src="${feature.properties.image}" />
        <div class="card-body">
          <div class="card-text">${description}</div>
        </div>
      </div>`;
    }

    // Ensure that if the map is zoomed out such that multiple
    // copies of the feature are visible, the popup appears
    // over the copy being pointed to.
    while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
      coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
    }

    // Populate the popup and set its coordinates
    // based on the feature found.
    popup.setLngLat(coordinates).setHTML(description).addTo(map);
  }

  function hidePopup() {
    popup.remove();
  }

  map.on("mouseenter", "points", showPopup);
  map.on("mouseenter", "photos", showPopup);
  map.on("mouseleave", "points", hidePopup);
  map.on("mouseleave", "photos", hidePopup);
});
