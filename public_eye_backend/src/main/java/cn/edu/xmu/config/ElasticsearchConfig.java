package cn.edu.xmu.config;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ElasticsearchConfig {
    @Bean(destroyMethod = "close")
    public RestHighLevelClient esClient() {
        return new RestHighLevelClient(
                RestClient.builder(
                        new HttpHost("1.92.94.117", 9200, "http")
                )
        );
    }
}