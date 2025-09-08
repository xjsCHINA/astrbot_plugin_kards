const puppeteer = require('puppeteer');
const fs = require('fs');

// 从命令行参数获取URL和输出文件路径
const [url, outputPath] = process.argv.slice(2);

if (!url || !outputPath) {
    console.error('缺少参数：需要URL和输出文件路径');
    process.exit(1);
}

async function takeScreenshot() {
    let browser;
    try {
        // 启动浏览器
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ],
            timeout: 60000
        });

        // 创建新页面
        const page = await browser.newPage();
        
        // 设置页面大小
        await page.setViewport({ width: 1200, height: 900 });
        
        // 导航到目标URL
        await page.goto(url, { 
            waitUntil: 'networkidle2',
            timeout: 60000
        });
        
        // 等待卡组加载完成（根据页面实际情况调整选择器）
        await page.waitForSelector('.deck-container', { timeout: 15000 });
        
        // 等待额外时间让图片加载
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 获取卡组区域并截图
        const deckElement = await page.$('.deck-container');
        if (deckElement) {
            await deckElement.screenshot({ path: outputPath });
        } else {
            // 备选方案：截取整个页面
            await page.screenshot({ path: outputPath, fullPage: true });
        }
        
        if (fs.existsSync(outputPath) && fs.statSync(outputPath).size > 0) {
            console.log('截图成功');
            process.exit(0);
        } else {
            console.error('截图文件生成失败');
            process.exit(1);
        }
        
    } catch (error) {
        console.error('截图失败:', error);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

takeScreenshot();
    