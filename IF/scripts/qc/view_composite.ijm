// view_composite.ijm  — ORTA foci TIFFs (autofoci_fiji_*.tif / foci_fiji_*.tif)
// Channels: 1 = raw, 2 = foci_labels (ids shuffled for display), 3 = nuclei.
// Open one of the TIFFs (File > Open...), then run this macro.

Stack.setDisplayMode("composite");   // address channels individually

Stack.setChannel(1);                  // raw -> grayscale, auto-contrast
run("Grays");
resetMinAndMax();

Stack.setChannel(2);                  // labels -> categorical colours
run("glasbey on dark");
setMinAndMax(0, 65535);               // shuffled ids span the full range -> distinct colours

Stack.setChannel(3);                  // nuclei -> grayscale
run("Grays");
resetMinAndMax();

run("Make Composite");
Stack.setActiveChannels("110");       // show raw + labels, hide nuclei (toggle in the C slider)
Stack.setChannel(2);
