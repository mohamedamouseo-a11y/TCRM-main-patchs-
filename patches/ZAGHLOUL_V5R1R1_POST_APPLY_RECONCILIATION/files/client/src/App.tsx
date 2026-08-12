// TCRM_INNOCALL_WEB_CALL_WIDGET_V1R3
import GlobalSearch from "./components/GlobalSearch";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch, Redirect, Router as WouterRouter, useLocation } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import { ThemeTokenProvider } from "./contexts/ThemeTokenContext";
import Login from "./pages/Login";
import AgentDashboard from "./pages/AgentDashboard";
import TeamDashboard from "./pages/TeamDashboard";
import SalesFunnelDashboard from "./pages/SalesFunnelDashboard";
import TaskSlaDashboard from "./pages/TaskSlaDashboard";
import LeadsList from "./pages/LeadsList";
import LeadProfile from "./pages/LeadProfile";
import AdminSettings from "./pages/AdminSettings";
import ImportLeads from "./pages/ImportLeads";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import SalesHeroesChat from "./components/SalesHeroesChat";
import ChatMonitor from "./pages/ChatMonitor";
import TosChatPage from "./pages/TosChatPage";
import TrashPage from "./pages/TrashPage";
import AuditLogPage from "./pages/AuditLogPage";
import CalendarPage from "./pages/CalendarPage";
import ClientPool from "./pages/ClientPool";
import ClientProfile from "./pages/ClientProfile";
import ClientWorkflow from "./pages/ClientWorkflow";
import RenewalPipeline from "./pages/RenewalPipeline";
import WorkflowDashboard from "./pages/WorkflowDashboard";
import TAMDashboard from "./pages/TAMDashboard";
import AMDashboard from "./pages/AMDashboard";
import AMCalendarPage from "./pages/AMCalendarPage";
import AMLeadDashboard from "./pages/AMLeadDashboard";
import CSATSurvey from "./pages/CSATSurvey";
import HelpCenter from "./pages/HelpCenter";
import AppRouteSeo from "./components/AppRouteSeo";
import BDDashboard from "./pages/BD/BDDashboard";
import BDAdvancedSettings from "./pages/BD/BDAdvancedSettings";
import DealsKanban from "./pages/BD/DealsKanban";
import DealDetail from "./pages/BD/DealDetail";
import CompaniesList from "./pages/BD/CompaniesList";
import ContactsList from "./pages/BD/ContactsList";
import BDSettings from "./pages/BD/BDSettings";
import BDAnalytics from "./pages/BD/BDAnalytics";
import BDEmailTemplates from "./pages/BD/BDEmailTemplates";
import BDQuote from "./pages/BD/BDQuote";
import BDCoaching from "./pages/BD/BDCoaching";
import BDPortal from "./pages/BD/BDPortal";
import NotificationSettings from "./pages/NotificationSettings";
import MetaCampaigns from "./pages/MetaCampaigns";
import TikTokCampaignsPage from "./pages/TikTokCampaignsPage";
import GoogleAdsCampaignsPage from "./pages/GoogleAdsCampaignsPage";
import SnapchatCampaignsPage from "./pages/SnapchatCampaignsPage";
import LinkedInAdsCampaignsPage from "./pages/LinkedInAdsCampaignsPage";
import EmailMarketingCenter from "./pages/EmailMarketingCenter";
import SupportCenter from "./pages/SupportCenter";
import SupportAdminInbox from "./pages/SupportAdminInbox";
import InboxPage from "./pages/Inbox";
import TaraAgentPage from "./pages/TaraAgentPage";
import ZaghloulAgentPage from "./pages/ZaghloulAgentPage";
import ZaghloulV5Page from "./pages/ZaghloulV5Page";
import WAGatewayInbox from "./pages/wa/WAGatewayInbox";
import WAGatewayAccounts from "./pages/wa/WAGatewayAccounts";
import WAGatewaySettings from "./pages/wa/WAGatewaySettings";
import THRSPage from "./pages/THRSPage";
import WorkspaceDashboard from "./pages/workspace/WorkspaceDashboard";
import WorkspaceProjects from "./pages/workspace/WorkspaceProjects";
import WorkspaceClients from "./pages/workspace/WorkspaceClients";
import WorkspaceShared from "./pages/workspace/WorkspaceShared";
import WorkspaceArchive from "./pages/workspace/WorkspaceArchive";
import WorkspaceSettings from "./pages/workspace/WorkspaceSettings";
import TDocsEditor from "./pages/workspace/TDocsEditor";
import TSheetsEditor from "./pages/workspace/TSheetsEditor";
import TSlidesEditor from "./pages/workspace/TSlidesEditor";
import SupportRequestDetail from "./pages/SupportRequestDetail";
import { InnoCallProvider } from "./contexts/InnoCallProvider";
import InnoCallWebCallWidget from "./components/InnoCallWebCallWidget";
import { useAuth } from "@/_core/hooks/useAuth";
import { isTaraModeratorRole } from "@/lib/roles";
import { isModeratorBlockedRoute } from "@shared/moderatorOperationalAccess";

const BASE_PATH = (import.meta.env.BASE_URL || "/").replace(/\/$/, "");

function ModeratorRouteGuard({ children }: { children: any }) {
  const { user, loading } = useAuth();
  const [location] = useLocation();
  if (loading) return <>{children}</>;
  const isModerator = isTaraModeratorRole(user?.role);
  if (isModerator && isModeratorBlockedRoute(location)) return <Redirect to="/tara" />;
  return <>{children}</>;
}

function GlobalSearchGated() {
  const { user } = useAuth();
  if (isTaraModeratorRole(user?.role)) return null;
  return <GlobalSearch />;
}

function Router() {
  return (
    <>
    <GlobalSearchGated />
    <Switch>
      <Route path="/" component={AgentDashboard} />
      <Route path="/login" component={Login} />
      <Route path="/dashboard" component={AgentDashboard} />
      <Route path="/bd" component={BDDashboard} />
      <Route path="/bd/deals" component={DealsKanban} />
      <Route path="/bd/deals/:id" component={DealDetail} />
      <Route path="/bd/companies" component={CompaniesList} />
      <Route path="/bd/contacts" component={ContactsList} />
      <Route path="/bd/settings" component={BDSettings} />
      <Route path="/bd/analytics" component={BDAnalytics} />
      <Route path="/bd/templates" component={BDEmailTemplates} />
      <Route path="/bd/coaching" component={BDCoaching} />
      <Route path="/bd/advanced" component={BDAdvancedSettings} />
      <Route path="/bd/quote/:id" component={BDQuote} />
      <Route path="/portal/:token" component={BDPortal} />
      <Route path="/team-dashboard" component={TeamDashboard} />
      <Route path="/sales-funnel" component={SalesFunnelDashboard} />
      <Route path="/task-sla" component={TaskSlaDashboard} />
      <Route path="/leads" component={LeadsList} />
      <Route path="/leads/:id" component={LeadProfile} />
      <Route path="/admin" component={AdminSettings} />
      <Route path="/settings" component={AdminSettings} />
      <Route path="/import" component={ImportLeads} />
      <Route path="/admin/chat" component={ChatMonitor} />
      <Route path="/chat" component={TosChatPage} />
      <Route path="/trash" component={TrashPage} />
      <Route path="/audit-log" component={AuditLogPage} />
      <Route path="/calendar" component={CalendarPage} />
      <Route path="/clients" component={ClientPool} />
      <Route path="/clients/:id/workflow" component={ClientWorkflow} />
      <Route path="/clients/:id" component={ClientProfile} />
      <Route path="/renewals" component={RenewalPipeline} />
      <Route path="/workflow-dashboard" component={WorkflowDashboard} />
      <Route path="/operations-dashboard" component={TAMDashboard} />
      <Route path="/am-dashboard" component={AMDashboard} />
      <Route path="/am-calendar" component={AMCalendarPage} />
      <Route path="/am-lead-dashboard" component={AMLeadDashboard} />
      <Route path="/tam-dashboard" component={TAMDashboard} />
      <Route path="/csat/:clientId" component={CSATSurvey} />
      <Route path="/notification-settings" component={NotificationSettings} />
      <Route path="/help-center">{() => <Redirect to="/ar/help-center" />}</Route>
      <Route path="/help-center/:slug">{(p: any) => <Redirect to={"/ar/help-center/" + p.slug} />}</Route>
      <Route path="/ar/help-center" component={HelpCenter} />
      <Route path="/ar/help-center/:slug" component={HelpCenter} />
      <Route path="/en/help-center" component={HelpCenter} />
      <Route path="/en/help-center/:slug" component={HelpCenter} />
      <Route path="/support-center" component={SupportCenter} />
      <Route path="/support-center/admin" component={SupportAdminInbox} />
      <Route path="/support-center/:id" component={SupportRequestDetail} />
      <Route path="/inbox" component={InboxPage} />
      <Route path="/wa-gateway/accounts" component={WAGatewayAccounts} />
      <Route path="/wa-gateway/settings" component={WAGatewaySettings} />
      <Route path="/wa-gateway" component={WAGatewayInbox} />
      <Route path="/tara" component={TaraAgentPage} />
      <Route path="/zaghloul" component={ZaghloulV5Page} />
      <Route path="/zaghloul-v5" component={ZaghloulV5Page} />
      <Route path="/zaghloul-legacy" component={ZaghloulAgentPage} />
      <Route path="/thrs" component={THRSPage} />
      <Route path="/meta-campaigns" component={MetaCampaigns} />
      <Route path="/tiktok-campaigns" component={TikTokCampaignsPage} />
      <Route path="/google-ads" component={GoogleAdsCampaignsPage} />
      <Route path="/email-marketing" component={EmailMarketingCenter} />
      <Route path="/snapchat-ads" component={SnapchatCampaignsPage} />
      <Route path="/linkedin-ads" component={LinkedInAdsCampaignsPage} />
      <Route path="/forgot-password" component={ForgotPassword} />
      <Route path="/reset-password" component={ResetPassword} />
      <Route path="/workspace" component={WorkspaceDashboard} />
      <Route path="/workspace/projects" component={WorkspaceProjects} />
      <Route path="/workspace/clients" component={WorkspaceClients} />
      <Route path="/workspace/shared" component={WorkspaceShared} />
      <Route path="/workspace/archive" component={WorkspaceArchive} />
      <Route path="/workspace/settings" component={WorkspaceSettings} />
      <Route path="/workspace/tdocs">{() => <Redirect to="/workspace" />}</Route>
      <Route path="/workspace/tsheets">{() => <Redirect to="/workspace/tsheets/new" />}</Route>
      <Route path="/workspace/tslides">{() => <Redirect to="/workspace" />}</Route>
      <Route path="/workspace/tdocs/:id" component={TDocsEditor} />
      <Route path="/workspace/tsheets/:id" component={TSheetsEditor} />
      <Route path="/workspace/tslides/:id" component={TSlidesEditor} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  </>
  );
}
function SalesHeroesChatGated() {
  const { user } = useAuth();
  const [loc] = useLocation();
  if (isTaraModeratorRole(user?.role)) return null;
  if (loc === "/chat" || loc.startsWith("/ar/help-center") || loc.startsWith("/en/help-center") || loc.startsWith("/help-center")) return null;
  return <SalesHeroesChat />;
}

function App() {
  return (
    <WouterRouter base={BASE_PATH}>
      <ErrorBoundary>
        <ThemeProvider defaultTheme="light" switchable>
          <LanguageProvider>
            <ThemeTokenProvider>
              <TooltipProvider>
                <InnoCallProvider>
                  <InnoCallWebCallWidget />
                  <Toaster />
                  <AppRouteSeo />
                  <ModeratorRouteGuard><Router /></ModeratorRouteGuard>
                  <SalesHeroesChatGated />
                </InnoCallProvider>
              </TooltipProvider>
            </ThemeTokenProvider>
          </LanguageProvider>
        </ThemeProvider>
      </ErrorBoundary>
    </WouterRouter>
  );
}
export default App;

// TARA_PRODUCTION_HARDENING_V1_ITEM3_MODERATOR
// TARA_MODERATOR_V1R4_OPERATIONAL_ACCESS

// TARA_MODERATOR_V1R5_FINAL_SCOPE
