import React, { useEffect, useState } from "react";
import Split, { SplitProps } from "react-split";
import { Box } from "@mui/material";
import "./style.css";

export interface SplitViewProps {
  id: string;
  children: React.ReactNode[];
  direction?: SplitProps["direction"];
  sizes?: SplitProps["sizes"];
  gutterSize?: SplitProps["gutterSize"];
}

/**
 * Renders a resizable split view layout, configurable for both horizontal and vertical directions.
 * Uses localStorage to persist and retrieve the last known sizes of the split panes, using the ID.
 *
 * @example
 * <SplitView id="main-split" direction="vertical" sizes={[30, 70]}>
 *   <ComponentOne />
 *   <ComponentTwo />
 * </SplitView>
 *
 * @param props - The component props.
 * @param props.id - Identifier to uniquely store the sizes of the panes.
 * @param props.children - Child components to be rendered within the split views.
 * @param props.direction - The orientation of the split view ("horizontal" or "vertical").
 * @param props.sizes - Initial sizes of each view in percentages. The array must sum to 100 and match the number of children.
 * @param props.gutterSize - The size of the gutter between split views. Defaults to 4.
 * @returns A React component displaying a split layout view with resizable panes.
 */
function SplitView({
  id,
  children,
  direction = "horizontal",
  sizes,
  gutterSize = 3,
}: SplitViewProps) {
  const numberOfChildren = React.Children.count(children);
  const defaultSizes = Array(numberOfChildren).fill(100 / numberOfChildren);
  const localStorageKey = `split-sizes-${id || "default"}-${direction}`;

  const [activeSizes, setActiveSizes] = useState(() => {
    const savedSizes = localStorage.getItem(localStorageKey);

    if (savedSizes) {
      return JSON.parse(savedSizes);
    }

    return sizes || defaultSizes;
  });

  useEffect(() => {
    // Update localStorage whenever activeSizes change.
    localStorage.setItem(localStorageKey, JSON.stringify(activeSizes));
  }, [activeSizes, localStorageKey]);

  return (
    <Box
      sx={{
        height: 1,
        width: 1,
        overflow: "auto",
      }}
    >
      <Split
        key={direction} // Force re-render when direction changes.
        className="split"
        direction={direction}
        sizes={activeSizes ?? defaultSizes}
        onDragEnd={setActiveSizes} // Update sizes on drag end.
        gutterSize={gutterSize}
        style={{
          display: "flex",
          flexDirection: direction === "horizontal" ? "row" : "column",
        }}
      >
        {children}
      </Split>
    </Box>
  );
}

export default SplitView;
