package cn.edu.xmu.service.impl;

import cn.edu.xmu.domain.po.Config;
import cn.edu.xmu.domain.po.Event;
import cn.edu.xmu.domain.po.Keyword;
import cn.edu.xmu.mapper.EventMapper;
import cn.edu.xmu.mapper.KeywordMapper;
import cn.edu.xmu.utils.PDFUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class ReportService {

    private final KeywordMapper keywordMapper;

    private final EventMapper eventMapper;

    private Map<Keyword, List<Event>> getReportData(Config config) {
        // 获取昨天的开始时间（00:00:00）
        LocalDateTime yesterdayStart = LocalDate.now().minusDays(0).atStartOfDay();
        // 获取昨天的结束时间（23:59:59）
        LocalDateTime yesterdayEnd = yesterdayStart.plusDays(1).minusSeconds(1);
        List<Keyword> topKeywords = keywordMapper.selectList(
                new LambdaQueryWrapper<Keyword>()
                .like(Keyword::getKeyword, '%' + config.getSearchKey() + '%')
                .between(Keyword::getUpdateTime, yesterdayStart, yesterdayEnd)
                .orderByDesc(Keyword::getHeat));
        // 创建一个 HashMap 来存储结果
        LinkedHashMap<Keyword, List<Event>> result = new LinkedHashMap<>();

        // 遍历每个 topKeyword，获取该关键词下热度最高的前10个事件
        for (Keyword keyword : topKeywords) {
            List<Event> topEvents = eventMapper.selectTop10EventsByKeywordId(keyword.getId());
            eventMapper.selectList(
                    new LambdaQueryWrapper<Event>()
                    .between(Event::getUpdateTime, yesterdayStart, yesterdayEnd)
                    .orderByAsc(Event::getHeat));
            result.put(keyword, topEvents);
        }
        return result;
    }

    public String generateReportPDFByConfig(Config config) throws Exception {
        Map<Keyword, List<Event>> reportData = getReportData(config);
        return PDFUtil.generateReportPdf(config, reportData);
    }
}
