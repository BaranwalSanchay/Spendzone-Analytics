import React from "react";
import { Sidebar } from "@/components/sidebar";
import { PageHeader } from "@/components/page-header";
import { ChartCard } from "@/components/chart-card";
import { FileText, Download, ExternalLink } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  TooltipProps,
} from "recharts";
import dashboardData from "../../public/data/dashboardData.json";

// Define TypeScript interfaces for the data
type ValueType = string | number | Array<string | number>;
type TooltipFormatter = (
  value: ValueType,
  name: string,
  props: TooltipProps<ValueType, string>
) => [string, string];

interface FormatterValue {
  value: number;
  name?: string;
  percent?: number;
}

const Appendix: React.FC = () => {
  const {
    quarterlyBreakdownData,
    demographicData,
    deviceBreakdownData,
    conversionRateData,
    dataSourcesTable,
    methodologyTable,
    documentsTable,
    glossaryItems,
  } = dashboardData.appendix;

  // Custom formatter to handle different types safely
  const formatCurrency: TooltipFormatter = (value) => {
    const numValue = typeof value === "number" ? value : Number(value);
    return [`$${(numValue / 1000).toFixed(1)}K`, ""];
  };

  const formatPercentage: TooltipFormatter = (value) => {
    const numValue = typeof value === "number" ? value : Number(value);
    return [`${numValue}%`, "Percentage"];
  };

  const formatConversionRate: TooltipFormatter = (value) => {
    const numValue = typeof value === "number" ? value : Number(value);
    return [`${numValue}%`, "Conversion Rate"];
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 p-6 overflow-y-auto ml-64">
        <PageHeader
          title="Appendix"
          subtitle="Technical details and methodology"
        />

        <Tabs defaultValue="data">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="data">Data Sources</TabsTrigger>
            <TabsTrigger value="methodology">Methodology</TabsTrigger>
            <TabsTrigger value="glossary">Glossary</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
          </TabsList>

          <TabsContent value="data" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Data Sources</CardTitle>
                <CardDescription>
                  Details of all data sources used in this marketing analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Source Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dataSourcesTable.map((source) => (
                      <TableRow key={source.id}>
                        <TableCell className="font-medium">
                          {source.name}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{source.type}</Badge>
                        </TableCell>
                        <TableCell>{source.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="methodology" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Methodology</CardTitle>
                <CardDescription>
                  Analytical approaches and methodologies used in this marketing
                  analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Methodology</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {methodologyTable.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">
                          {item.name}
                        </TableCell>
                        <TableCell>{item.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            
          </TabsContent>

          <TabsContent value="glossary">
            <Card>
              <CardHeader>
                <CardTitle>Marketing Terminology Glossary</CardTitle>
                <CardDescription>
                  Definitions of key marketing terms used throughout the
                  dashboard
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {glossaryItems.map((item, index) => (
                    <div key={index} className="border-b pb-3">
                      <h3 className="font-bold">{item.term}</h3>
                      <p className="text-sm text-muted-foreground">
                        {item.definition}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Supporting Documents</CardTitle>
                <CardDescription>
                  Download additional documents and resources
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documentsTable.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell className="font-medium flex items-center">
                          <FileText className="h-4 w-4 mr-2 text-muted-foreground" />
                          {doc.name}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{doc.type}</Badge>
                        </TableCell>
                        <TableCell>
                          {new Date(doc.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>{doc.size}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                          >
                            <Download className="h-4 w-4 mr-1" />
                            Download
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>External Resources</CardTitle>
                <CardDescription>
                  Links to relevant marketing resources and research
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  <li className="flex items-center">
                    <ExternalLink className="h-4 w-4 mr-2 text-muted-foreground" />
                    <a href="#" className="text-primary hover:underline">
                      Marketing Benchmarks 2023
                    </a>
                  </li>
                  <li className="flex items-center">
                    <ExternalLink className="h-4 w-4 mr-2 text-muted-foreground" />
                    <a href="#" className="text-primary hover:underline">
                      Industry Trends Report
                    </a>
                  </li>
                  <li className="flex items-center">
                    <ExternalLink className="h-4 w-4 mr-2 text-muted-foreground" />
                    <a href="#" className="text-primary hover:underline">
                      Attribution Modeling Guide
                    </a>
                  </li>
                  <li className="flex items-center">
                    <ExternalLink className="h-4 w-4 mr-2 text-muted-foreground" />
                    <a href="#" className="text-primary hover:underline">
                      Budget Optimization Whitepaper
                    </a>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Appendix;
