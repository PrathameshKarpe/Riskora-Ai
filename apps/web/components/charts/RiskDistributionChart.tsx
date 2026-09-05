"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { RiskLevel } from "@/lib/types";

const COLORS: Record<RiskLevel, string> = {
  LOW:      "#10b981",
  MEDIUM:   "#f59e0b",
  HIGH:     "#f97316",
  CRITICAL: "#ef4444",
};

const ORDER: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

interface Props {
  data: Record<RiskLevel, number>;
}

export function RiskDistributionChart({ data }: Props) {
  const chartData = ORDER.filter((l) => data[l] != null).map((level) => ({
    level,
    count: data[level] ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="level"
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          cursor={{ fill: "#f8fafc" }}
          contentStyle={{
            fontSize: 12,
            border: "1px solid #e2e8f0",
            borderRadius: 6,
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
          formatter={(value) => [Number(value ?? 0), "Transactions"]}
        />
        <Bar dataKey="count" radius={[3, 3, 0, 0]} maxBarSize={40}>
          {chartData.map((entry) => (
            <Cell key={entry.level} fill={COLORS[entry.level]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
