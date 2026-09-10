import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bell, ChevronDown, LogOut, Menu, Search, Settings, User as UserIcon } from "lucide-react";
import type { User } from "../../types";
import { Avatar } from "../ui/Avatar";
import { notificationService, NotificationItem } from "../../services/notificationService";

interface Props { user: User; onMenu: () => void; onLogout: () => void }

export function Topbar({ user, onMenu, onLogout }: Props) {
  const [openUser, setOpenUser] = useState(false);
  const [openNotif, setOpenNotif] = useState(false);
  const [realNotifications, setRealNotifications] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const base = `/${user.role}`;

  useEffect(() => {
    notificationService
      .getMyNotifications(5)
      .then((res) => {
        setRealNotifications(res.notifications || []);
        setUnread(res.unread_count || 0);
      })
      .catch((err) => console.warn("Could not load notifications for topbar:", err));
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur sm:px-6">
      <button onClick={onMenu} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"><Menu className="h-5 w-5" /></button>
      <div className="relative hidden flex-1 md:block md:max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input placeholder="Search skills, opportunities, mentors…" className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-3 text-sm placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-indigo-100" />
      </div>
      <div className="ml-auto flex items-center gap-2">
        <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"><Search className="h-5 w-5" /></button>
        <div className="relative">
          <button onClick={() => { setOpenNotif((v) => !v); setOpenUser(false); }} className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100">
            <Bell className="h-5 w-5" />
            {unread > 0 && <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">{unread}</span>}
          </button>
          {openNotif && (
            <div className="absolute right-0 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3"><p className="text-sm font-semibold">Notifications</p><Link to={`${base}/notifications`} onClick={() => setOpenNotif(false)} className="text-xs font-medium text-indigo-600">View all</Link></div>
              <ul className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
                {realNotifications.length === 0 ? (
                  <li className="px-4 py-6 text-center text-xs text-slate-400">No notifications available</li>
                ) : (
                  realNotifications.map((n) => (
                    <li key={n.notification_id} className="flex gap-3 px-4 py-3 hover:bg-slate-50">
                      <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${n.read ? "bg-slate-200" : "bg-indigo-500"}`} />
                      <div>
                        <p className="text-sm font-medium text-slate-800">{n.title}</p>
                        <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{n.message}</p>
                        <p className="mt-1 text-[11px] text-slate-400">{new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</p>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}
        </div>
        <div className="relative">
          <button onClick={() => { setOpenUser((v) => !v); setOpenNotif(false); }} className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-100">
            <Avatar src={user.avatar} name={user.name} size="sm" />
            <span className="hidden text-left sm:block"><span className="block text-sm font-semibold leading-tight text-slate-800">{user.name}</span><span className="block text-[11px] capitalize text-slate-500">{user.role}</span></span>
            <ChevronDown className="hidden h-4 w-4 text-slate-400 sm:block" />
          </button>
          {openUser && (
            <div className="absolute right-0 mt-2 w-52 overflow-hidden rounded-2xl border border-slate-200 bg-white py-1 shadow-xl">
              <Link to={`${base}/profile`} onClick={() => setOpenUser(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"><UserIcon className="h-4 w-4" /> My Profile</Link>
              <Link to={`${base}/settings`} onClick={() => setOpenUser(false)} className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"><Settings className="h-4 w-4" /> Settings</Link>
              <button onClick={onLogout} className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50"><LogOut className="h-4 w-4" /> Sign out</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
