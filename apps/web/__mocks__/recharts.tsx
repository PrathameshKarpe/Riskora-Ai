// Lightweight recharts mock for Jest (avoids ESM issues with D3)
import React from "react";

const noop = () => null;

export const BarChart = ({ children }: { children?: React.ReactNode }) => <div data-testid="BarChart">{children}</div>;
export const Bar = noop;
export const XAxis = noop;
export const YAxis = noop;
export const CartesianGrid = noop;
export const Tooltip = noop;
export const ResponsiveContainer = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
export const Cell = noop;
export const PieChart = noop;
export const Pie = noop;
export const LineChart = noop;
export const Line = noop;
export const Legend = noop;
