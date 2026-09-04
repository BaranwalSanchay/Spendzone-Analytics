import React, { useState } from 'react';
import { Header } from '@/components/header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, FileText, Printer, Share2, Eye, ChevronDown } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';

// Hardcoded report content sections
const REPORT_CONTENT = {
  'executive-summary': {
    title: 'Executive Summary',
    content: `The executive summary provides a high-level overview of the company's performance based on the analyzed data, highlighting key insights and findings across various dimensions.

#### 1. **Data Overview**
- The dataset comprises **1,648,824 rows** and **51 columns**, encompassing customer orders, product details, marketing expenditures, and environmental data.
- Key metrics include:
  - Order Date
  - Gross Merchandise Value (GMV)
  - Units Sold
  - Maximum Retail Price (MRP)
  - Marketing expenditures across channels such as:
    - TV
    - Digital
    - Sponsorship
    - Others

#### 2. **Marketing Expenditure**
- The company allocates its marketing budget across multiple channels, with **Sponsorship** and **Digital** being the most significant investments, averaging **$84.67** and **$12.62**, respectively.
- Other notable channels include **Online Marketing** ($24.37), **SEM** ($31.93), and **Affiliates** ($6.97).
- **TV** and **Radio** expenditures are relatively low, with averages of **$6.14** and **$0.00**, respectively.

#### 3. **Sales and Revenue Performance**
- The average **GMV (Gross Merchandise Value)** per order is **$2,459.73**, with a maximum GMV of **$226,947.00**.
- The average **List Price** of products is **$2,574.40**, with a maximum of **$1,701.56**.
- The average **Discount** percentage is **4.20%**, indicating moderate price reductions to drive sales.

#### 4. **Customer and Product Insights**
- The average **NPS (Net Promoter Score)** is **44.4**, indicating moderate customer satisfaction.
- The most common **Product Type** is **1**, with the majority of products falling under the **CE (Consumer Electronics)** category, specifically **CameraAccessory** and **CameraTripod** subcategories.
- The average **Units** sold per order is **1**, with a maximum of **5 units** per order.

#### 5. **Operational Insights**
- The average **SLA (Service Level Agreement)** for orders is **5 days**, with a maximum of **1,006 days**.
- The majority of orders (93.5%) are marked as **non-holiday sales**.

#### 6. **Environmental and Market Trends**
- Environmental data, including temperature, precipitation, and snowfall, is available and could be used to analyze seasonal trends in sales.
- The **Stock Index** is relatively stable, with an average of **1,210.0**.

#### 7. **Key Insights and Recommendations**
- **Focus on High-Performing Marketing Channels**: Sponsorship and Digital channels show significant investment and should be optimized further.
- **Analyze Seasonal Trends**: Incorporate environmental data to identify correlations between weather patterns and sales performance.
- **Improve Customer Satisfaction**: While the NPS score is moderate, further analysis of customer feedback could help improve satisfaction levels.
- **Optimize Pricing Strategy**: The average discount rate is low, suggesting potential for further price adjustments to boost sales.

This executive summary provides a concise overview of the company's performance, highlighting key areas for further investigation to drive growth and efficiency.`
  },
  'business-context': {
    title: 'Business Context',
    content: `#### Market Analysis and Insights: Marketing Expenditure and ROI

The business context for the company is shaped by broader market trends and the performance of its marketing initiatives. Below is an analysis of the marketing expenditure, performance, and market insights:

### Key Findings:

1. **Median Profit ROI for Successful Campaigns in 2023**:
   - The median profit-based ROI for successful advertising campaigns worldwide in 2023 was **2.43 US dollars**. This indicates that for every dollar invested in marketing, companies, on average, generated a return of $2.43. (Source: Statista)

2. **Marketing Budget as a Percentage of Revenue**:
   - In 2023, the average marketing budget was **9.1% of total revenue**, which is the lowest it has been in seven years, excluding the immediate impact of the pandemic. This reflects a potential shift in how companies are allocating their resources toward marketing. (Source: Innovation Visual)

3. **Year-over-Year Change in Marketing Budgets**:
   - Marketing budgets dropped from an average of **9.1% of company revenue in 2023** to **7.7% in 2024**, representing a **15% year-over-year decrease**. This trend suggests that companies are reducing their marketing spend, possibly due to economic uncertainties or a reevaluation of marketing strategies. (Source: Gartner)

4. **Industry-Specific Marketing Budgets**:
   - In 2023, the average marketing budget was **9.1% of total income**, with industries like retail and e-commerce allocating up to **15% of their revenue** to marketing. This highlights the variability in marketing spend across different sectors. (Source: Asymmetric)`
  },
  'marketing-performance': {
    title: 'Marketing Performance',
    content: `#### Overview of Marketing Effectiveness
The marketing strategies implemented over the past year have demonstrated a strong ability to drive revenue and achieve business objectives. By analyzing the data, it is evident that certain marketing channels have outperformed others, contributing significantly to the overall success of the campaigns.

#### Top Performing Marketing Channels
The following channels have been identified as the top performers based on their contribution to revenue:

- **Sponsorship**: 
  - Investment: 84.67
  - Contribution to GMV: This channel has been the most significant contributor to revenue, leveraging strategic partnerships and brand visibility to maximize reach and impact.

- **Search Engine Marketing (SEM)**:
  - Investment: 31.93
  - Contribution to GMV: SEM has proven highly effective due to its targeted approach, ensuring that marketing efforts reach the most relevant audience, thus driving conversions.

- **Online Marketing**:
  - Investment: 24.37
  - Contribution to GMV: The versatility and precision of online marketing tactics have made this channel a key driver of revenue, with a strong return on investment.

#### Rationale for Top Performing Channels
The success of these channels can be attributed to several factors:

- **Sponsorship**: The high investment in sponsorship has paid off by enhancing brand visibility and credibility, attracting a broader audience and establishing trust, which are crucial for driving sales.

- **SEM**: The effectiveness of SEM lies in its ability to target specific demographics and keywords, ensuring that marketing efforts are concentrated where they are most likely to convert, thus optimizing the return on investment.

- **Online Marketing**: The digital nature of this channel allows for precise targeting and measurable outcomes, making it a cost-effective and efficient method for reaching potential customers.

#### Conclusion
The past year's marketing strategies have been successful, with Sponsorship, SEM, and Online Marketing emerging as the top performers. These channels have effectively utilized their investments to drive significant revenue contributions. The insights gained from this analysis will be invaluable for shaping future marketing strategies, ensuring continued success and growth.`
  },
  'performance-drivers': {
    title: 'Performance Drivers',
    content: `The primary factors that contributed to the company's revenue growth are multifaceted and can be attributed to various product categories, order payment types, and other key performance indicators (KPIs). 

### Product Performance
The top-performing products are those within the categories of CameraAccessory, MobileAccessory, and HomeDecor. These products have shown significant revenue growth, with CameraAccessory being the highest performer. The product categories of CE, Fashion, and Home and Kitchen have also demonstrated strong performance.

### Order Payment Types
The order payment types that have contributed to revenue growth are COD, Online, and Offline. These payment types have been the most popular among customers, with COD being the highest performer.

### Key Performance Indicators (KPIs)
The KPIs that have driven revenue growth include:
* Average Monthly NPS Score: 49.46
* Average Discount Percentage: 44.61%
* Most Common Discount Range: 45.0%
* Correlation between Current Month NPS and Next Month GMV: -0.1234
* Correlation between GMV and Discount Percentage: -0.2286
* Correlation between GMV and SLA: -0.1245

### Top Performing Products and KPIs
The top performing products are those with high GMV and low SLA. For example, products with GMV above $10,000 and SLA below 5 days. The top KPIs are:
* Average Monthly NPS Score
* Average Discount Percentage
* Most Common Discount Range
* Correlation between Current Month NPS and Next Month GMV
* Correlation between GMV and Discount Percentage
* Correlation between GMV and SLA

### Data Insights
The data analysis has revealed the following insights:
* The company's revenue growth has been significant over the past few years, with some product categories and order payment types performing better than others.
* The company's customer satisfaction has been good, with some customers being more satisfied than others.
* The company's employees have performed well, with some employees performing better than others.
* The top-performing products, categories, subcategories, verticals, order payment types, order dates, years, months, days, date/time, max temperatures, min temperatures, mean temperatures, heat deg days, cool deg days, total rain, total snow, total precip, snow on ground, total investments, TV, digital, sponsorship, content marketing, online marketing, affiliates, SEM, radio, other, NPS scores, stock indices, is sales, weeks, list prices, product types, discounts, payday weeks, and holiday weeks have been identified.

### Statistical Analysis
The statistical analysis has revealed the following correlations:
* Correlation between Current Month NPS and Next Month GMV: -0.1234
* Correlation between GMV and Discount Percentage: -0.2286
* Correlation between GMV and SLA: -0.1245

These correlations suggest that customer satisfaction may not be driving future sales as expected, and that higher discounts tend to lead to lower GMV. Additionally, orders with higher GMV tend to have shorter SLA. 

The data insights and statistical analysis provide a comprehensive understanding of the performance drivers that have contributed to the company's revenue growth.`
  },
  'marketing-roi': {
    title: 'Marketing ROI',
    content: `The return on investment (ROI) analysis for the marketing initiatives undertaken last year reveals key insights into the performance of various marketing channels. Based on the data analysis, the top-performing marketing channels are:

* SEM, with a ROI value of 1.8553
* Online marketing, with a ROI value of 1.5799
* Digital, with a ROI value of 0.1072

The attributed revenue and attribution percentages for each channel are:
* SEM: $1,848,612,397.15 (45.58% of total GMV)
* Online marketing: $3,684,567,948.01 (90.85% of total GMV)
* Digital: $33,763,543.39 (0.83% of total GMV)

The marginal ROI values for each channel are:
* SEM: 319.89%
* Online marketing: -4.79%
* Digital: 47.43%

The ROI analysis also reveals that the channels with negative ROI are:
* Affiliates, with a ROI value of -0.5301
* Sponsorship, with a ROI value of -0.2294
* Content Marketing, with a ROI value of 0.0338
* TV, with a ROI value of -0.0156

The baseline revenue (intercept) for current months is $72,519,892.37, and for next months is $758,378,075.65.

### Channel Performance

The performance of each marketing channel can be summarized as follows:
* SEM: High ROI, high attributed revenue, and high marginal ROI
* Online marketing: High attributed revenue, but negative marginal ROI
* Digital: Low attributed revenue, but high marginal ROI
* Affiliates: Negative ROI, negative attributed revenue, and low marginal ROI
* Sponsorship: Negative ROI, negative attributed revenue, and low marginal ROI
* Content Marketing: Low ROI, low attributed revenue, and low marginal ROI
* TV: Negative ROI, negative attributed revenue, and low marginal ROI

### ROI Trends

The ROI trends for each channel can be summarized as follows:
* SEM: Increasing ROI, increasing attributed revenue, and increasing marginal ROI
* Online marketing: Decreasing ROI, decreasing attributed revenue, and decreasing marginal ROI
* Digital: Increasing ROI, increasing attributed revenue, and increasing marginal ROI
* Affiliates: Decreasing ROI, decreasing attributed revenue, and decreasing marginal ROI
* Sponsorship: Decreasing ROI, decreasing attributed revenue, and decreasing marginal ROI
* Content Marketing: Increasing ROI, increasing attributed revenue, and increasing marginal ROI
* TV: Decreasing ROI, decreasing attributed revenue, and decreasing marginal ROI

The data suggests that the top-performing marketing channels are SEM, Online marketing, and Digital, with high ROI values and high attributed revenue. The channels with negative ROI are Affiliates, Sponsorship, Content Marketing, and TV, with low ROI values and low attributed revenue. The marginal ROI values for each channel provide further insights into the performance of each channel, with SEM and Digital having high marginal ROI values, and Online marketing having a negative marginal ROI value.`
  },
  'budget-allocation': {
    title: 'Budget Allocation',
    content: `The analysis of the current marketing budget and performance of the company reveals key insights into the most effective allocation of the marketing budget for future campaigns. Based on the data, the following findings are noteworthy:

* The top marketing channels by investment are:
  + Sponsorship: 84.67%
  + SEM: 31.93%
  + Online marketing: 24.37%
  + Digital: 12.62%
  + Affiliates: 6.97%
  + TV: 6.14%
  + Content Marketing: 3.44%
* The marketing channels with the highest investment have the highest return, with Sponsorship being the most effective channel, as it has the highest value in the top 10 orders by GMV.

The data suggests that the current marketing budget is allocated effectively, with a focus on Sponsorship, SEM, and Online marketing. These channels have the highest investment and are driving the most revenue.

### Key Statistics

* TV: 6.14%
* Digital: 12.62%
* Sponsorship: 84.67%
* Content Marketing: 3.44%
* Online marketing: 24.37%
* Affiliates: 6.97%
* SEM: 31.93%

These statistics indicate that the marketing budget is being allocated effectively, with a focus on the channels that are driving the most revenue. The data suggests that the current marketing strategy is effective, and the budget allocation is optimized to achieve the best possible return on investment.


The data analysis reveals that the top 10 orders by GMV are driven by Sponsorship, with a value of 84.67%. This suggests that Sponsorship is the most effective marketing channel for driving revenue. The data also suggests that SEM and Online marketing are effective channels, with values of 31.93% and 24.37%, respectively.

Overall, the analysis suggests that the current marketing budget allocation is effective, with a focus on the channels that are driving the most revenue. The data provides insights into the most effective marketing channels and can be used to inform future marketing strategies and budget allocations.`
  },
  'implementation': {
    title: 'Implementation',
    content: `The implementation of the proposed marketing budget changes is a critical step in improving the marketing performance of the company. Based on the analysis, a strategic plan can be outlined to achieve this goal.

### Strategic Plan for Implementing Marketing Budget Changes

The strategic plan for implementing marketing budget changes involves the following steps:

1. **Develop a Strategic Marketing Budget Plan**: Create a comprehensive marketing budget plan that aligns with the company's overall business goals and objectives. This plan should include a detailed breakdown of marketing expenses, revenue projections, and key performance indicators (KPIs) to measure marketing effectiveness.
2. **Conduct Market Research and Analysis**: Conduct market research to understand the target audience, industry trends, and competitor analysis. This will help identify opportunities and challenges, and inform marketing strategies and tactics.
3. **Establish Clear Marketing Goals and Objectives**: Establish clear marketing goals and objectives that align with the company's overall business objectives. This will help focus marketing efforts and ensure that all marketing activities are working towards common goals.
4. **Develop a Marketing Mix**: Develop a marketing mix that includes a combination of marketing strategies and tactics, such as digital marketing, social media, content marketing, email marketing, and paid advertising.
5. **Implement and Optimize Marketing Campaigns**: Implement and optimize marketing campaigns to achieve marketing goals and objectives. This includes tracking and analyzing campaign performance, identifying areas for improvement, and making data-driven decisions to optimize marketing spend.
6. **Foster a Performance-Driven Culture**: Foster a performance-driven culture within the marketing team, where team members are empowered to make data-driven decisions and are held accountable for marketing performance.
7. **Continuously Monitor and Evaluate Marketing Performance**: Continuously monitor and evaluate marketing performance, using KPIs and other metrics to measure marketing effectiveness and identify areas for improvement.

### Strategies to Improve Marketing Performance

To improve marketing performance, the following strategies can be implemented:

* **Audience Segmentation**: Segment the target audience to create targeted marketing campaigns that resonate with specific audience groups.
* **Outbound Marketing Channels**: Utilize outbound marketing channels, such as paid advertising and email marketing, to reach new customers and drive conversions.
* **Inbound Marketing Channels**: Utilize inbound marketing channels, such as content marketing and social media, to attract and engage with customers and drive conversions.
* **Lead Management and Nurturing**: Implement lead management and nurturing strategies to convert leads into customers and drive revenue growth.
* **Marketing Automation**: Implement marketing automation tools to streamline marketing processes, improve efficiency, and enhance customer engagement.

### Prospective Timeline for Boosting Marketing and Scaling Up Business

To boost marketing and scale up the business, the following prospective timeline can be outlined:

* **Month 1-3**: Develop a strategic marketing budget plan, conduct market research and analysis, and establish clear marketing goals and objectives.
* **Month 4-6**: Develop a marketing mix, implement and optimize marketing campaigns, and foster a performance-driven culture within the marketing team.
* **Month 7-9**: Continuously monitor and evaluate marketing performance, using KPIs and other metrics to measure marketing effectiveness and identify areas for improvement.
* **Month 10-12**: Scale up marketing efforts, utilizing strategies such as audience segmentation, outbound marketing channels, inbound marketing channels, lead management and nurturing, and marketing automation.

By following this strategic plan, implementing the outlined strategies, and adhering to the prospective timeline, the company can improve marketing performance, boost marketing efforts, and scale up the business to achieve long-term growth and success.`
  }
};

// Section definitions for the UI
const sectionDefinitions = [
  { id: 'executive-summary', title: 'Executive Summary' },
  { id: 'business-context', title: 'Business Context' },
  { id: 'marketing-performance', title: 'Marketing Performance' },
  { id: 'performance-drivers', title: 'Performance Drivers' },
  { id: 'marketing-roi', title: 'Marketing ROI' },
  { id: 'budget-allocation', title: 'Budget Allocation' },
  { id: 'implementation', title: 'Implementation' }
];

const Report = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('executive-summary');
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  
  // PDF file path
  const pdfPath = '/assets/sample-report.pdf';

  const handleDownload = () => {
    // Create a link element
    const link = document.createElement('a');
    link.href = pdfPath;
    link.download = 'marketing-analysis-report.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast({
      title: 'Report Downloaded',
      description: 'Your report has been downloaded successfully.',
    });
  };

  const handleViewPdf = () => {
    setPdfViewerOpen(true);
  };

  const handlePrint = () => {
    toast({
      description: 'Preparing document for printing...',
    });
    window.print();
  };

  const handleShare = () => {
    toast({
      title: 'Share Report',
      description: 'Sharing functionality will be available soon.',
    });
  };

  // Custom component to render markdown content with proper styling
  const MarkdownContent = ({ content }) => {
    if (!content) return <p>No content available</p>;
    
    // Define custom components for markdown elements
    const components = {
      // Handle different heading levels
      h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-6 mb-4" {...props} />,
      h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-5 mb-3" {...props} />,
      h3: ({ node, ...props }) => <h3 className="text-lg font-bold mt-4 mb-2" {...props} />,
      h4: ({ node, ...props }) => <h4 className="text-base font-semibold mt-3 mb-2" {...props} />,
      h5: ({ node, ...props }) => <h5 className="text-sm font-semibold mt-3 mb-1" {...props} />,
      h6: ({ node, ...props }) => <h6 className="text-sm font-medium mt-2 mb-1" {...props} />,
      
      // Improve list styling
      ul: ({ node, ...props }) => <ul className="list-disc pl-6 my-4 space-y-2" {...props} />,
      ol: ({ node, ...props }) => <ol className="list-decimal pl-6 my-4 space-y-2" {...props} />,
      li: ({ node, ...props }) => <li className="my-1" {...props} />,
      
      // Enhance code and inline code - Fix for inline code rendering
      code: ({ node, inline, ...props }) => 
        inline ? 
          <code className="px-1 py-0.5 bg-muted/50 rounded text-sm font-mono inline-block" {...props} /> : 
          <pre className="p-4 bg-muted rounded-md overflow-x-auto my-4">
            <code className="text-sm font-mono" {...props} />
          </pre>,
      
      // Better paragraph spacing
      p: ({ node, ...props }) => <p className="my-3" {...props} />,
      
      // Enhance tables if needed
      table: ({ node, ...props }) => <table className="w-full border-collapse my-6" {...props} />,
      th: ({ node, ...props }) => <th className="border p-2 bg-muted font-medium text-left" {...props} />,
      td: ({ node, ...props }) => <td className="border p-2" {...props} />,
      
      // Improve blockquotes
      blockquote: ({ node, ...props }) => 
        <blockquote className="pl-4 border-l-4 border-muted italic my-4" {...props} />
    };

    return (
      <div className="prose prose-sm max-w-none dark:prose-invert prose-code:inline-block">
        <ReactMarkdown components={components}>
          {content}
        </ReactMarkdown>
      </div>
    );
  };
  
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Marketing Performance Report</h1>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleViewPdf}>
              <Eye className="h-4 w-4 mr-2" />
              View PDF
            </Button>
            <Button variant="outline" size="sm" onClick={handlePrint}>
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button variant="outline" size="sm" onClick={handleShare}>
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
            <Button size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Report Overview</CardTitle>
            <CardDescription>
              Generated on {new Date().toLocaleDateString()} for Q2 2023
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              This report provides a comprehensive analysis of marketing performance, ROI, and budget allocation recommendations based on the data you've uploaded.
            </p>
            
            {/* Table of Contents */}
            <div className="mt-4 border-t pt-4">
              <h3 className="font-medium mb-2">Table of Contents</h3>
              <ul className="space-y-1">
                {sectionDefinitions.map((section) => (
                  <li key={section.id} className="flex items-center">
                    <ChevronDown className="h-4 w-4 mr-2 text-primary" />
                    <button 
                      className="text-primary hover:underline"
                      onClick={() => setActiveTab(section.id)}
                    >
                      {section.title}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        <Tabs 
          defaultValue="executive-summary" 
          value={activeTab} 
          onValueChange={setActiveTab}
          className="mb-6"
        >
          {/* Display all tabs in a single row */}
          <TabsList className="flex flex-wrap w-full">
            {sectionDefinitions.map((section) => (
              <TabsTrigger 
                key={section.id} 
                value={section.id}
                className="flex-1 min-width-0 text-xs md:text-sm whitespace-nowrap overflow-hidden text-ellipsis"
              >
                {section.title}
              </TabsTrigger>
            ))}
          </TabsList>
          
          {/* Tab content for each section */}
          {sectionDefinitions.map((section) => (
            <TabsContent key={section.id} value={section.id} className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>{section.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <MarkdownContent 
                    content={REPORT_CONTENT[section.id]?.content || 'Content not available'} 
                  />
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
        
        <Card>
          <CardHeader>
            <CardTitle>Download Options</CardTitle>
            <CardDescription>Export this report in various formats</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center justify-center" onClick={handleDownload}>
              <FileText className="h-8 w-8 mb-2" />
              <span className="font-medium">PDF Report</span>
              <span className="text-xs text-muted-foreground mt-1">Complete report with all visualizations</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center justify-center" onClick={handleDownload}>
              <FileText className="h-8 w-8 mb-2" />
              <span className="font-medium">Excel Data</span>
              <span className="text-xs text-muted-foreground mt-1">Raw data and calculations</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center justify-center" onClick={handleDownload}>
              <FileText className="h-8 w-8 mb-2" />
              <span className="font-medium">Presentation</span>
              <span className="text-xs text-muted-foreground mt-1">Executive slides for stakeholders</span>
            </Button>
          </CardContent>
          <CardFooter className="border-t px-6 py-4">
            <p className="text-sm text-muted-foreground">
              Need a custom report format? Contact your account manager for personalized reporting options.
            </p>
          </CardFooter>
        </Card>
      </main>

      {/* PDF Viewer Dialog */}
      <Dialog open={pdfViewerOpen} onOpenChange={setPdfViewerOpen}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle>Marketing Analysis Report</DialogTitle>
          </DialogHeader>
          <div className="flex-1 w-full h-full min-h-[60vh]">
            <iframe 
              src={`${pdfPath}#toolbar=0&navpanes=0`} 
              className="w-full h-full border-0" 
              title="Marketing Analysis Report"
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setPdfViewerOpen(false)}>
              Close
            </Button>
            <Button onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Report;