export type UserRole = "PATIENT" | "DOCTOR";

export interface AddonDefinition {
  id: string;
  name: string;
  path: string;
  roles: UserRole[];
  icon?: string;
}

export const ADDONS: AddonDefinition[] = [
  {
    id: "dashboard",
    name: "Dashboard",
    path: "/dashboard",
    roles: ["PATIENT", "DOCTOR"],
    icon: "📊",
  },
  {
    id: "appointments",
    name: "Appointments",
    path: "/dashboard/appointments",
    roles: ["PATIENT", "DOCTOR"],
    icon: "📅",
  },
  {
    id: "profile",
    name: "Profile",
    path: "/dashboard/profile",
    roles: ["PATIENT", "DOCTOR"],
    icon: "👤",
  },
  {
    id: "assistant",
    name: "Assistant",
    path: "/dashboard/assistant",
    roles: ["PATIENT", "DOCTOR"],
    icon: "💬",
  },
];

export function getAddonsForRole(role: UserRole): AddonDefinition[] {
  return ADDONS.filter((a) => a.roles.includes(role));
}
